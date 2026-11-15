"""Helpers for the AE-312 labs (import mawj as M).

Loading the Mawj Telecom data, the reference cost model, a prefix-cache model, a small local
embedding, graders for the three applications, one call to a free hosted model with a stand-in,
and the reference values behind the safety-net cells. Everything about Mawj is synthetic.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import time
import urllib.request
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
REF = DATA / "reference"
ARTIFACTS = LABS / "artifacts"
QUICK = os.environ.get("MAWJ_QUICK", "0") == "1"
TIERS = ["tier-s", "tier-m", "tier-l"]


def pick(full, quick):
    """The small value in quick mode (MAWJ_QUICK=1), the full one otherwise."""
    return quick if QUICK else full


def check(condition, message):
    print(("✅ " if condition else "❌ ") + message)
    if not condition:
        raise AssertionError(message)


def sar(x, digits=2):
    return f"SAR {x:,.{digits}f}"


def lab_dir(name):
    d = ARTIFACTS / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- loading
def read_jsonl(path):
    path = Path(path)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


@lru_cache(maxsize=None)
def prices():
    return json.loads((DATA / "prices.json").read_text(encoding="utf-8"))


def read_usage(path):
    df = pd.read_csv(path, keep_default_na=False, parse_dates=["ts"])
    return df


def usage():
    """A month of gateway log rows: one row per attempt of a request."""
    return read_usage(DATA / "usage.csv.gz")


def invoice():
    return pd.read_csv(DATA / "invoice.csv")


def keys():
    return pd.read_csv(DATA / "gateway" / "keys.csv", keep_default_na=False)


def gpu_hours():
    return pd.read_csv(DATA / "gpu_hours.csv")


def load_json(rel):
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


def tasks(app):
    return read_jsonl(DATA / "eval" / f"tasks_{app}.jsonl")


def outputs():
    return pd.DataFrame(read_jsonl(DATA / "eval" / "outputs.jsonl.gz"))


# ---------------------------------------------------------------- reference values (safety nets)
def _plain(v):
    if isinstance(v, pd.DataFrame):
        return {"__frame__": json.loads(v.to_json(orient="records", date_format="iso"))}
    if isinstance(v, pd.Series):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, dict):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, np.generic):
        return v.item()
    return v


def keep(name, value):
    """Write a reference value. Only the course author's solution run does this (MAWJ_WRITE_REF=1)."""
    if os.environ.get("MAWJ_WRITE_REF") == "1":
        REF.mkdir(parents=True, exist_ok=True)
        (REF / f"{name}.json").write_bytes((json.dumps(_plain(value), ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    return value


def reference(name):
    """The result of the reference solution for an exercise, so later cells run when it was skipped."""
    v = json.loads((REF / f"{name}.json").read_text(encoding="utf-8"))
    if isinstance(v, dict) and "__frame__" in v:
        return pd.DataFrame(v["__frame__"])
    return v


# ---------------------------------------------------------------- the reference cost model
def add_cost(df, region="global", batch=False):
    """Add cost_sar: what the provider bills for each row (Lab 1.1 builds this by hand).

    Uncached input, cached input and output plus reasoning tokens at the tier's prices, for the
    statuses the provider bills (ok and timeout). Rows on the leased node cost nothing per token.
    """
    p = prices()
    out = df.copy()
    tier = out["model"].map(lambda m: p["tiers"].get(m))
    pin = tier.map(lambda t: t["input"] if t else 0.0)
    pc = tier.map(lambda t: t["cached_input"] if t else 0.0)
    po = tier.map(lambda t: t["output"] if t else 0.0)
    billed = out["status"].isin(p["rules"]["billed_statuses"])
    cost = ((out["input_tokens"] - out["cached_tokens"]) * pin + out["cached_tokens"] * pc
            + (out["output_tokens"] + out["reasoning_tokens"]) * po) / 1e6
    mult = (p["in_kingdom_premium"] if region == "in-kingdom" else 1.0) * (p["batch_discount"] if batch else 1.0)
    out["cost_sar"] = cost.where(billed, 0.0) * mult
    return out


def with_register(df):
    """Join the key register: team, app and env as the register names them (Lab 1.3 looks harder)."""
    return df.merge(keys()[["key_id", "team", "app", "env"]], on="key_id", how="left")


def tag(df, name):
    """The value of one tag ("app=khulasa;caller=fasil" -> tag(df, "caller") is "fasil"), "" when absent."""
    return df["tags"].str.extract(rf"(?:^|;){name}=([^;]*)", expand=False).fillna("")


# ---------------------------------------------------------------- tokens and the prefix cache
_TOKEN = re.compile(r"\w+|[^\w\s]")


@lru_cache(maxsize=4096)
def tokenize(text):
    """A plain stand-in tokenizer: words cut into pieces of four characters, punctuation apart.

    Real tokenizers differ by model; this one is deterministic and close enough to count with.
    """
    out = []
    for w in _TOKEN.findall(text):
        out.extend(w[i:i + 4] for i in range(0, len(w), 4))
    return tuple(out)


def count_tokens(text):
    return len(tokenize(text))


@lru_cache(maxsize=None)
def _prompt_parts():
    return ((DATA / "prompts" / "anis_instructions.md").read_text(encoding="utf-8"), load_json("prompts/policy_sections.json"))


def render_part(req, part, sort_policies=False):
    instructions, sections = _prompt_parts()
    if part == "clock":
        return f"Current time: {req['clock']}"
    if part == "profile":
        return req["profile"]
    if part == "instructions":
        return instructions
    if part == "policies":
        order = sorted(req["section_order"]) if sort_policies else req["section_order"]
        return "\n\n".join(sections[s] for s in order)
    if part == "history":
        return "\n".join(req["history"])
    if part == "question":
        return req["question"]
    raise KeyError(part)


CURRENT_LAYOUT = ["clock", "profile", "instructions", "policies", "history", "question"]


def build_prompt(req, layout=CURRENT_LAYOUT, sort_policies=False):
    """The prompt of one replayed request as text, its parts in the order of `layout`."""
    return "\n\n".join(render_part(req, part, sort_policies) for part in layout)


def prompt_tokens(req, layout=CURRENT_LAYOUT, sort_policies=False):
    toks = []
    for part in layout:
        if part == "policies":
            _, sections = _prompt_parts()
            for s in (sorted(req["section_order"]) if sort_policies else req["section_order"]):
                toks.extend(tokenize(sections[s]))
        else:
            toks.extend(tokenize(render_part(req, part)))
    return toks


def first_difference(a, b, context=60):
    """Where two prompts stop being equal: (token index, the text of each around that place)."""
    ta, tb = tokenize(a), tokenize(b)
    n = next((i for i, (x, y) in enumerate(zip(ta, tb)) if x != y), min(len(ta), len(tb)))
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return n, a[max(0, i - 20):i + context].replace("\n", " "), b[max(0, i - 20):i + context].replace("\n", " ")


class PrefixCache:
    """A model of a provider's prompt cache.

    A request reuses the longest prefix it shares with an earlier request, counted in blocks of
    `block` tokens, when that prefix is at least `min_tokens` long and was last used less than
    `ttl_s` seconds ago. Every use refreshes the entry. The defaults follow the published rules of
    two large providers (see the course sources); real caches differ in detail.
    """

    def __init__(self, min_tokens=1024, block=128, ttl_s=300):
        self.min_tokens, self.block, self.ttl_s = min_tokens, block, ttl_s
        self.seen = {}

    def lookup(self, tokens, t):
        """Return (cached_tokens, written_tokens) for a prompt sent at time t (seconds), then store it."""
        h, cached, alive, hashes = hashlib.md5(), 0, True, []
        for k in range(len(tokens) // self.block):
            h.update("\x1f".join(tokens[k * self.block:(k + 1) * self.block]).encode("utf-8"))
            d = h.digest()
            hashes.append(d)
            if alive and t - self.seen.get(d, -1e18) < self.ttl_s:
                cached = (k + 1) * self.block
            else:
                alive = False
        if cached < self.min_tokens:
            cached = 0
        for d in hashes:
            self.seen[d] = t
        written = len(hashes) * self.block - cached if len(hashes) * self.block >= self.min_tokens else 0
        return cached, written


def replay_prompts(reqs, layout=CURRENT_LAYOUT, sort_policies=False, cache=None):
    """Send every replayed request through a prefix cache: one row per request."""
    cache = cache or PrefixCache()
    rows = []
    for r in reqs:
        toks = prompt_tokens(r, layout, sort_policies)
        cached, written = cache.lookup(toks, r["t"])
        rows.append({"t": r["t"], "session": r["session"], "turn": r["turn"], "input_tokens": len(toks), "cached_tokens": cached,
                     "written_tokens": written, "output_tokens": r["output_tokens"], "reasoning_tokens": 0, "status": "ok", "model": "tier-m"})
    return pd.DataFrame(rows)


def ttft_ms(df, tier="tier-m"):
    """Time to first token from the synthetic latency model of the price sheet."""
    m = prices()["latency_model_ms"][tier]
    return m["base"] + m["per_1k_uncached"] * (df["input_tokens"] - df["cached_tokens"]) / 1000 + m["per_1k_cached"] * df["cached_tokens"] / 1000


# ---------------------------------------------------------------- a small local embedding
def embed(texts, dim=256):
    """Hashed character 3-grams, L2-normalised: a lexical stand-in for an embedding model.

    No download and no key. It shares the weakness that matters here with real embeddings:
    "activate roaming" and "deactivate roaming" land close together.
    """
    out = np.zeros((len(texts), dim), dtype=np.float32)
    for i, t in enumerate(texts):
        s = "  " + re.sub(r"\s+", " ", t.lower().strip()) + "  "
        for j in range(len(s) - 2):
            out[i, zlib.crc32(s[j:j + 3].encode("utf-8")) % dim] += 1.0
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.maximum(norms, 1e-9)


# ---------------------------------------------------------------- graders
_ARABIC = re.compile(r"[؀-ۿ]")


def arabic_share(text):
    letters = [c for c in text if c.isalpha()]
    return sum(bool(_ARABIC.match(c)) for c in letters) / max(1, len(letters))


def language_of(text):
    return "ar" if arabic_share(text) > 0.5 else "en"


def grade(app, task, text):
    """Pass or fail for one output of an application, by code (Lab 2.1 writes the first one by hand)."""
    exp = task["expected"]
    if app == "anis":
        return bool(text) and all(s in text + " " for s in exp["must_include"]) \
            and language_of(text) == exp["lang"]
    try:
        got = json.loads(text)
    except (ValueError, TypeError):
        return False
    if not isinstance(got, dict):
        return False
    return all(got.get(k) == v for k, v in exp.items())


# ---------------------------------------------------------------- one call to a hosted model, or the stand-in
def _load_env():
    f = LABS / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
LIVE_MODELS = {
    "tier-s": os.environ.get("MAWJ_TIER_S", "liquid/lfm-3-1.7b:free"),
    "tier-m": os.environ.get("MAWJ_TIER_M", "google/gemma-4-26b-a4b-it:free"),
    "tier-l": os.environ.get("MAWJ_TIER_L", "google/gemma-4-31b-it:free"),
}
BASE_URL = os.environ.get("MAWJ_BASE_URL", "https://openrouter.ai/api/v1")


def live():
    return bool(os.environ.get("OPENROUTER_API_KEY")) and os.environ.get("MAWJ_LIVE", "1") != "0"


def chat(tier, system, user, stand_in=None, max_tokens=300):
    """One chat call to the free hosted model that plays `tier`. Returns a dict.

    Without a key (or with MAWJ_LIVE=0, or when the free model does not answer) the supplied
    output `stand_in` is returned and marked source="stand-in", so the lab still runs.
    """
    if live():
        body = json.dumps({"model": LIVE_MODELS[tier], "max_tokens": max_tokens, "temperature": 0,
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode("utf-8")
        req = urllib.request.Request(BASE_URL + "/chat/completions", data=body, headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                use = data.get("usage", {})
                return {"text": data["choices"][0]["message"]["content"] or "", "source": LIVE_MODELS[tier],
                        "input_tokens": use.get("prompt_tokens", 0), "output_tokens": use.get("completion_tokens", 0),
                        "cached_tokens": (use.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
                        "latency_ms": int((time.time() - t0) * 1000)}
            except Exception as e:                      # a busy free model, a rate limit, a refused key
                last = e
                time.sleep(2 + 3 * attempt)
        print(f"   live call failed ({type(last).__name__}); using the stand-in")
    s = stand_in or {}
    return {"text": s.get("text", ""), "source": "stand-in", "input_tokens": s.get("input_tokens", 0),
            "output_tokens": s.get("output_tokens", 0), "cached_tokens": s.get("cached_tokens", 0), "latency_ms": s.get("latency_ms", 0)}


# ---------------------------------------------------------------- energy beside cost
def add_energy(df):
    """Add energy_wh from the assumed figures of data/hosting/energy.json (synthetic)."""
    e = load_json("hosting/energy.json")
    w = e["wh_per_1k_tokens"]
    out = df.copy()
    win = out["model"].map(lambda m: w.get(m, {}).get("input", 0.0))
    wout = out["model"].map(lambda m: w.get(m, {}).get("output", 0.0))
    out["energy_wh"] = ((out["input_tokens"] - out["cached_tokens"]) * win + out["cached_tokens"] * win * e["cached_input_factor"]
                        + (out["output_tokens"] + out["reasoning_tokens"]) * wout) / 1000
    return out
