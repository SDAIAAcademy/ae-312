"""Mawj Telecom: the synthetic case data of AE-312.

Standard library only, a fixed seed, the same bytes on every run:

    python prepare_data.py            # writes labs/data/
    python prepare_data.py --check    # rebuilds in memory and compares with labs/data/

Everything here is invented: the operator, its customers, the provider, the prices, the invoice.
The planted problems are listed in solutions/answer_key.md.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULTS = dict(
    seed=312,
    month_start="2026-10-01",
    days=31,
    incident_day=17,          # a tool outage and a provider incident on this day of the month
    anis_sessions=18000,
    khulasa_calls=26000,
    pilot_requests=4500,
    fasil_sessions=3200,
    fasil_b_from_day=16,      # the cheaper configuration is tried from this day
    fasil_b_share=0.5,
    experiment_requests=1100,
    direct_share=0.013,       # spend on a provider key that bypasses the gateway
    node_hours_per_night=8,
    khulasa_tier="tier-m",
    anis_layout_broken=True,
)

PRICES = {
    "synthetic": True,
    "currency": "SAR",
    "unit": "per million tokens",
    "tiers": {
        "tier-s": {"input": 0.60, "cached_input": 0.06, "output": 2.40},
        "tier-m": {"input": 3.00, "cached_input": 0.30, "output": 12.00},
        "tier-l": {"input": 12.00, "cached_input": 1.20, "output": 48.00},
    },
    "rules": {
        "input_tokens_include_cached": True,
        "reasoning_tokens_billed_as": "output",
        "billed_statuses": ["ok", "timeout"],
        "note": "The provider bills a request it started to answer, also when the client gave up "
                "(timeout). It does not bill a request it refused (error).",
    },
    "batch_discount": 0.5,
    "in_kingdom_premium": 1.30,
    "local": {"model": "local-os", "node_sar_per_hour": 14.0, "billing": "per leased hour, used or not"},
    "latency_model_ms": {
        "note": "synthetic: time to first token = base + per_1k_uncached * uncached/1000 + per_1k_cached * cached/1000",
        "tier-s": {"base": 180, "per_1k_uncached": 22, "per_1k_cached": 3},
        "tier-m": {"base": 260, "per_1k_uncached": 38, "per_1k_cached": 5},
        "tier-l": {"base": 420, "per_1k_uncached": 70, "per_1k_cached": 9},
    },
}

KEYS = [
    # key_id, team, app, env, owner, note
    ("key-anis-prod", "customer-care", "anis", "prod", "Taghreed Al-Omran", ""),
    ("key-anis-stg", "customer-care", "anis", "staging", "Taghreed Al-Omran", ""),
    ("key-anis-dev", "customer-care", "anis", "dev", "Taghreed Al-Omran", ""),
    ("key-shared-legacy", "contact-centre-analytics", "khulasa", "prod", "Qutaiba Al-Ajaji",
     "issued before Maabar had keys per application; read the tags"),
    ("key-khulasa-pilot", "contact-centre-analytics", "khulasa", "staging", "Qutaiba Al-Ajaji",
     "nightly pilot on the leased accelerator node"),
    ("key-fasil-prod", "billing-operations", "fasil", "prod", "Humoud Al-Rubaian", ""),
    ("key-fasil-stg", "billing-operations", "fasil", "staging", "Humoud Al-Rubaian", ""),
    ("key-platform-test", "platform", "smoke-tests", "dev", "Murtada Al-Awami", ""),
]

TEAMS = [
    ("customer-care", "CC-410", "Taghreed Al-Omran"),
    ("contact-centre-analytics", "CC-430", "Qutaiba Al-Ajaji"),
    ("billing-operations", "CC-520", "Humoud Al-Rubaian"),
    ("network-analytics", "CC-610", "(no key issued)"),
    ("platform", "CC-900", "Murtada Al-Awami"),
]

CARE_HOURS = [1, 1, .5, .3, .2, .2, .5, 1.5, 3, 5, 7, 8, 8, 7, 6, 6, 6, 6, 7, 8, 8, 7, 5, 3]
WORK_HOURS = [0, 0, 0, 0, 0, 0, 0, .5, 4, 7, 8, 8, 7, 7, 7, 6, 6, 5, 4, 3, 2, 1.5, 1, 0]
OFFICE_HOURS = [0, 0, 0, 0, 0, 0, 0, .3, 5, 8, 9, 9, 8, 8, 8, 7, 5, 2, .6, .3, 0, 0, 0, 0]

PLANS = [("Mawj 55", 55, "10 GB"), ("Mawj 85", 85, "30 GB"), ("Mawj 115", 115, "60 GB"), ("Mawj 165", 165, "200 GB"),
         ("Bayt 100", 229, "100 Mbps"), ("Bayt 300", 299, "300 Mbps"), ("Bayt 500", 379, "500 Mbps")]

TOPICS = [
    # id, English name, Arabic name, fee in SAR, working days
    ("P-01", "SIM replacement", "استبدال الشريحة", 25, 1), ("P-02", "eSIM activation", "تفعيل الشريحة الإلكترونية", 0, 1),
    ("P-03", "number transfer", "نقل الرقم", 0, 3), ("P-04", "late payment", "التأخر في السداد", 10, 15),
    ("P-05", "refund of a charge", "استرداد مبلغ", 0, 14), ("P-06", "contract exit", "إنهاء العقد", 20, 5),
    ("P-07", "roaming pack", "باقة التجوال", 99, 7), ("P-08", "fibre installation", "تركيب الألياف", 150, 4),
    ("P-09", "router replacement", "استبدال الموجّه", 80, 2), ("P-10", "plan change", "تغيير الباقة", 0, 1),
    ("P-11", "ownership transfer", "نقل الملكية", 30, 2), ("P-12", "bill dispute", "الاعتراض على الفاتورة", 0, 10),
    ("P-13", "data top-up", "شحن البيانات", 15, 1), ("P-14", "voicemail", "البريد الصوتي", 0, 1),
    ("P-15", "call waiting", "انتظار المكالمات", 0, 1), ("P-16", "5G access", "خدمة الجيل الخامس", 0, 1),
    ("P-17", "family line", "خط العائلة", 35, 1), ("P-18", "temporary suspension", "الإيقاف المؤقت", 12, 1),
    ("P-19", "international calls", "المكالمات الدولية", 0, 1), ("P-20", "device instalments", "أقساط الأجهزة", 0, 3),
    ("P-21", "address change", "تغيير العنوان", 0, 2), ("P-22", "lost phone", "فقدان الهاتف", 0, 1),
    ("P-23", "paper bill", "الفاتورة الورقية", 5, 1), ("P-24", "priority care", "العناية المميزة", 45, 1),
]
SERVICES = [("roaming", "التجوال"), ("voicemail", "البريد الصوتي"), ("call waiting", "انتظار المكالمات"),
            ("5G access", "الجيل الخامس"), ("international calls", "المكالمات الدولية"), ("the paper bill", "الفاتورة الورقية")]


def pick_weighted(rng, weights):
    return rng.choices(range(len(weights)), weights=weights)[0]


def writer_gz(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0) as gz:
            gz.write(text.encode("utf-8"))


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)


# --------------------------------------------------------------------------------------------
# Usage traces
# --------------------------------------------------------------------------------------------
USAGE_COLS = ["request_id", "ts", "key_id", "tags", "session_id", "customer_id", "step", "attempt", "status",
              "model", "reasoning", "input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens",
              "latency_ms", "lang"]


class Usage:
    def __init__(self, p):
        self.p = p
        self.start = datetime.fromisoformat(p["month_start"])
        self.rows = []
        self.day_w = []
        for d in range(p["days"]):
            wd = (self.start + timedelta(days=d)).weekday()
            self.day_w.append((0.7 if wd == 4 else 0.85 if wd == 5 else 1.0) * (1 + 0.004 * d))

    def when(self, rng, hours, day=None):
        d = pick_weighted(rng, self.day_w) if day is None else day
        h = pick_weighted(rng, hours)
        return self.start + timedelta(days=d, hours=h, minutes=rng.randrange(60), seconds=rng.randrange(60))

    def in_incident(self, t, lo=13, hi=15):
        return t.day == self.p["incident_day"] and lo <= t.hour <= hi

    def call(self, rng, t, key, tags, sess, cust, step, model, reasoning, n_in, cached, n_out, n_reason, lang,
             client_timeout_ms=30000):
        """One logical call: zero or more failed attempts, then (usually) a success. Returns (end time, ok)."""
        per_out = {"tier-s": 6, "tier-m": 12, "tier-l": 22, "local-os": 30}[model]
        base = {"tier-s": 350, "tier-m": 500, "tier-l": 800, "local-os": 1500}[model]
        attempt = 1
        while True:
            storm = self.in_incident(t) and model != "local-os"
            r = rng.random()
            p_to, p_err = (0.38, 0.05) if storm else (0.006, 0.010)
            if attempt < 4 and r < p_to:
                frac = rng.uniform(0.1, 0.6)
                self.rows.append([t, key, tags, sess, cust, step, attempt, "timeout", model, reasoning, n_in, cached,
                                  int(n_out * frac), int(n_reason * frac), client_timeout_ms, lang])
                t += timedelta(milliseconds=client_timeout_ms + rng.randrange(500, 3000))
            elif attempt < 4 and r < p_to + p_err:
                lat = rng.randrange(150, 900)
                self.rows.append([t, key, tags, sess, cust, step, attempt, "error", model, reasoning, n_in, 0, 0, 0, lat, lang])
                t += timedelta(milliseconds=lat + rng.randrange(500, 2500))
            else:
                lat = int(base + 0.012 * (n_in - cached) + per_out * (n_out + n_reason) * rng.uniform(0.85, 1.2))
                self.rows.append([t, key, tags, sess, cust, step, attempt, "ok", model, reasoning, n_in, cached, n_out, n_reason, lat, lang])
                return t + timedelta(milliseconds=lat), True
            attempt += 1


def gen_usage(p):
    U = Usage(p)
    rng = random.Random(p["seed"])
    customers = [f"c{n:05d}" for n in range(60000)]

    # ---- Anis, the care assistant: a long stable instruction and policy block resent on every turn
    for s in range(p["anis_sessions"]):
        t = U.when(rng, CARE_HOURS)
        cust, lang = rng.choice(customers), ("ar" if rng.random() < 0.62 else "en")
        turns = 1
        while turns < 7 and rng.random() < 0.52:
            turns += 1
        base = 1150 + rng.randrange(5300, 6300) + 120
        hist = 0
        for k in range(1, turns + 1):
            q = rng.randrange(18, 70)
            out = int(rng.randrange(90, 240) * (1.2 if lang == "ar" else 1.0))
            cached = 0 if p["anis_layout_broken"] else ((base + hist) // 128) * 128
            t, _ = U.call(rng, t, "key-anis-prod", "", f"a{s:06d}", cust, k, "tier-m", "off", base + hist + q, cached, out, 0, lang)
            hist += q + out
            t += timedelta(seconds=rng.randrange(20, 90))
    for i in range(500):
        t = U.when(rng, OFFICE_HOURS)
        U.call(rng, t, "key-anis-stg", "", f"as{i:05d}", "c-test", 1, "tier-m", "off", rng.randrange(7000, 7900), 0, rng.randrange(90, 240), 0, rng.choice(["ar", "en"]))
    for i in range(350):
        t = U.when(rng, OFFICE_HOURS)
        U.call(rng, t, "key-anis-dev", "", f"ad{i:05d}", "c-test", 1, "tier-l", rng.choice(["off", "high"]), rng.randrange(7000, 9500), 0, rng.randrange(120, 400), rng.randrange(0, 900), rng.choice(["ar", "en"]))

    # ---- Khulasa, the call-summary job: one long transcript per call, a stable 1,100-token instruction first
    calls = []
    for c in range(p["khulasa_calls"]):
        t = U.when(rng, WORK_HOURS)
        cust, lang = rng.choice(customers), ("ar" if rng.random() < 0.7 else "en")
        transcript = int(min(30000, max(2500, rng.lognormvariate(9.05, 0.45))))
        cached = 1024 if rng.random() < 0.85 else 0
        tags = "app=khulasa" if rng.random() < 0.92 else ""
        sess = f"k{c:06d}"
        n_before = len(U.rows)
        U.call(rng, t, "key-shared-legacy", tags, sess, cust, 1, p["khulasa_tier"], "off", 1100 + transcript, cached, rng.randrange(240, 420), 0, lang)
        urgent = 1 if rng.random() < 0.08 else 0
        calls.append((sess, n_before, urgent, round(transcript / 420, 1)))
    # the nightly pilot: a sample of the day's calls summarised again on the leased node
    for i in range(p["pilot_requests"]):
        d = pick_weighted(rng, U.day_w)
        t = U.start + timedelta(days=d, hours=rng.randrange(0, p["node_hours_per_night"]), minutes=rng.randrange(60), seconds=rng.randrange(60))
        transcript = int(min(30000, max(2500, rng.lognormvariate(9.05, 0.45))))
        U.call(rng, t, "key-khulasa-pilot", "app=khulasa", f"kp{i:05d}", rng.choice(customers), 1, "local-os", "off", 1100 + transcript, 0, rng.randrange(240, 420), 0, "ar" if rng.random() < 0.7 else "en")
    # another team's experiment on the shared key, in one week
    for i in range(p["experiment_requests"]):
        t = U.when(rng, OFFICE_HOURS, day=rng.randrange(7, 12))
        U.call(rng, t, "key-shared-legacy", "app=netlab-exp;team=network-analytics", f"x{i:05d}", "c-none", 1, "tier-l", "high",
               rng.randrange(5000, 9000), 0, rng.randrange(500, 1100), rng.randrange(1200, 2800), "en", client_timeout_ms=60000)

    # ---- Fasil, the billing-dispute agent: a tool loop whose context grows with every step
    fasil = []
    for s in range(p["fasil_sessions"]):
        t = U.when(rng, OFFICE_HOURS)
        day = (t - U.start).days + 1
        config = "B" if (day >= p["fasil_b_from_day"] and rng.random() < p["fasil_b_share"]) else "A"
        model = "tier-l" if config == "A" else "tier-m"
        cust, lang = rng.choice(customers), ("ar" if rng.random() < 0.6 else "en")
        sess = f"f{s:06d}"
        loop = day == p["incident_day"] and 12 <= t.hour <= 16 and rng.random() < 0.85
        long_ctx = (not loop) and rng.random() < 0.04
        steps = (3 + sum(rng.random() < 0.46 for _ in range(7))) if config == "A" else (4 + sum(rng.random() < 0.5 for _ in range(7)))
        if loop:
            steps = rng.randrange(30, 56) if rng.random() < 0.9 else rng.randrange(60, 81)
        huge = long_ctx and rng.random() < 0.07
        ctx, prev_in, kind = 3400 + rng.randrange(200, 900), 0, ("loop" if loop else "long" if long_ctx else "plain")
        for k in range(1, steps + 1):
            cached = (prev_in // 128) * 128
            out = rng.randrange(150, 420)
            reason = rng.randrange(900, 2600) if config == "A" else rng.randrange(700, 2000)
            t, _ = U.call(rng, t, "key-fasil-prod", "", sess, cust, k, model, "high", ctx, cached, out, reason, lang, client_timeout_ms=60000)
            prev_in = ctx
            tool = rng.randrange(700, 2600)
            if loop and k >= 3:
                tool = rng.randrange(90, 160)              # the billing system answers "pending" again and again
            if long_ctx and k >= 2:                     # a tool without paging returns the itemised bills again
                tool = rng.randrange(60000, 90000) if huge else rng.randrange(22000, 34000)
            ctx += out + tool
            t += timedelta(seconds=rng.randrange(1, 4))
        fasil.append((sess, config, kind, day, lang))
        # some sessions ask Khulasa for a summary of the customer's earlier calls
        if rng.random() < 0.4:
            U.call(rng, t, "key-shared-legacy", "app=khulasa;caller=fasil", f"kf{s:06d}", cust, 1, p["khulasa_tier"], "off",
                   1100 + rng.randrange(6000, 16000), 1024, rng.randrange(240, 420), 0, lang)
    for i in range(320):
        t = U.when(rng, OFFICE_HOURS)
        U.call(rng, t, "key-fasil-stg", "", f"fs{i:05d}", "c-test", 1 + i % 5, "tier-l", "high", rng.randrange(3500, 14000), 0, rng.randrange(150, 420), rng.randrange(900, 2600), rng.choice(["ar", "en"]))
    for i in range(400):
        t = U.when(rng, OFFICE_HOURS)
        U.call(rng, t, "key-platform-test", "", f"t{i:05d}", "c-test", 1, "tier-s", "off", rng.randrange(40, 200), 0, rng.randrange(5, 40), 0, "en")

    order = sorted(range(len(U.rows)), key=lambda i: (U.rows[i][0], i))
    rid = {}
    out = []
    for n, i in enumerate(order, start=1):
        r = U.rows[i]
        rid[i] = f"r{n:06d}"
        out.append([rid[i], r[0].strftime("%Y-%m-%dT%H:%M:%S")] + r[1:])
    khulasa_calls = [(rid[n_before], sess, urgent, minutes) for sess, n_before, urgent, minutes in calls]
    return out, khulasa_calls, fasil


def cost_of(row, prices=PRICES):
    """The provider's bill for one usage row (the reference cost model)."""
    status, model = row[8], row[9]
    if model not in prices["tiers"] or status not in prices["rules"]["billed_statuses"]:
        return 0.0
    pr = prices["tiers"][model]
    n_in, cached, n_out, reason = row[11], row[12], row[13], row[14]
    return ((n_in - cached) * pr["input"] + cached * pr["cached_input"] + (n_out + reason) * pr["output"]) / 1e6


def gen_invoice(p, usage):
    lines, n = [], 0
    agg = {}
    for r in usage:
        status, model = r[8], r[9]
        if model in PRICES["tiers"] and status in ("ok", "timeout"):
            a = agg.setdefault(model, [0, 0, 0])
            a[0] += r[11] - r[12]
            a[1] += r[12]
            a[2] += r[13] + r[14]
    gateway_total = 0.0
    for model in sorted(agg):
        pr = PRICES["tiers"][model]
        for item, qty, unit in (("input tokens", agg[model][0], pr["input"]), ("cached input tokens", agg[model][1], pr["cached_input"]),
                                ("output tokens", agg[model][2], pr["output"])):
            n += 1
            amount = round(qty * unit / 1e6, 2)
            gateway_total += amount
            lines.append([n, "up-maabar-01", item, model, qty, "tokens", unit, amount])
    # a provider key that was never registered on the gateway
    direct = gateway_total * p["direct_share"] / (1 - p["direct_share"])
    pr = PRICES["tiers"]["tier-l"]
    q_in, q_out = int(direct * 0.5 / pr["input"] * 1e6), int(direct * 0.5 / pr["output"] * 1e6)
    for item, qty, unit in (("input tokens", q_in, pr["input"]), ("output tokens", q_out, pr["output"])):
        n += 1
        lines.append([n, "up-direct-7q2f", item, "tier-l", qty, "tokens", unit, round(qty * unit / 1e6, 2)])
    hours = p["node_hours_per_night"] * p["days"]
    n += 1
    lines.append([n, "node-lease", "accelerator node, on demand", "local-os", hours, "hours", PRICES["local"]["node_sar_per_hour"],
                  round(hours * PRICES["local"]["node_sar_per_hour"], 2)])
    return lines


def gen_gpu_hours(p, usage):
    start = datetime.fromisoformat(p["month_start"])
    per = {}
    for r in usage:
        if r[9] == "local-os" and r[8] == "ok":
            k = (r[1][:10], int(r[1][11:13]))
            a = per.setdefault(k, [0, 0, 0])
            a[0] += 1
            a[1] += r[11]
            a[2] += r[13]
    rows = []
    for d in range(p["days"]):
        date = (start + timedelta(days=d)).strftime("%Y-%m-%d")
        for h in range(p["node_hours_per_night"]):
            a = per.get((date, h), [0, 0, 0])
            rows.append([date, h, 1, round(min(60.0, a[0] * 0.6), 1), a[0], a[1], a[2]])
    return rows


# --------------------------------------------------------------------------------------------
# Evaluation tasks and supplied outputs
# --------------------------------------------------------------------------------------------
CONFIGS = [("tier-s", "off"), ("tier-s", "high"), ("tier-m", "off"), ("tier-m", "high"), ("tier-l", "off"), ("tier-l", "high"), ("local-os", "off")]
# passes out of 50 per language (en, ar) for each configuration
QUOTA = {
    "anis": {("tier-s", "off"): (46, 37), ("tier-s", "high"): (46, 39), ("tier-m", "off"): (48, 47), ("tier-m", "high"): (49, 47),
             ("tier-l", "off"): (49, 48), ("tier-l", "high"): (49, 49), ("local-os", "off"): (46, 42)},
    "khulasa": {("tier-s", "off"): (48, 46), ("tier-s", "high"): (48, 46), ("tier-m", "off"): (48, 48), ("tier-m", "high"): (49, 48),
                ("tier-l", "off"): (49, 48), ("tier-l", "high"): (49, 49), ("local-os", "off"): (48, 47)},
    "fasil": {("tier-s", "off"): (29, 26), ("tier-s", "high"): (36, 34), ("tier-m", "off"): (39, 37), ("tier-m", "high"): (46, 45),
              ("tier-l", "off"): (44, 42), ("tier-l", "high"): (48, 47), ("local-os", "off"): (40, 38)},
}
FLOORS = {"anis": 0.92, "khulasa": 0.92, "fasil": 0.90}
REASONS = ["billing", "coverage", "roaming", "fibre_fault", "plan_change", "sim"]
RESOLUTIONS = ["resolved", "callback", "escalated", "refund_issued"]


def plan_sheet():
    lines = ["Mawj plan sheet (synthetic)"]
    for name, price, allowance in PLANS:
        lines.append(f"- {name}: SAR {price} a month, {allowance}")
    for pid, en, _ar, fee, days in TOPICS[:8]:
        lines.append(f"- {en}: fee SAR {fee}, completed within {days} working days")
    return "\n".join(lines)


def gen_tasks(p):
    rng = random.Random(p["seed"] + 1)
    tasks = {"anis": [], "khulasa": [], "fasil": []}
    sheet = plan_sheet()
    for lang in ("en", "ar"):
        for i in range(50):
            tid = f"A-{lang}-{i + 1:02d}"
            if i % 2 == 0:
                name, price, allowance = PLANS[(i // 2) % len(PLANS)]
                amount = allowance.split()[0]
                q = (f"How much is the {name} plan a month and what does it include?" if lang == "en"
                     else f"كم سعر باقة {name} في الشهر وماذا تشمل؟")
                good = (f"The {name} plan costs SAR {price} a month and includes {allowance}." if lang == "en"
                        else f"باقة {name} سعرها {price} ريالا في الشهر وتشمل {allowance}.")
                other = PLANS[(i // 2 + 2) % len(PLANS)]
                bad = (f"The {name} plan costs SAR {other[1]} a month and includes {other[2]}." if lang == "en"
                       else f"باقة {name} سعرها {other[1]} ريالا في الشهر وتشمل {other[2]}.")
                must = [str(price), amount]
            else:
                pid, en, ar, fee, days = TOPICS[(i // 2) % 8]
                q = (f"What is the fee for {en} and how long does it take?" if lang == "en" else f"كم رسوم {ar} وكم يستغرق الطلب؟")
                good = (f"The fee for {en} is SAR {fee} and the request is completed within {days} working days." if lang == "en"
                        else f"رسوم {ar} هي {fee} ريالا ويكتمل الطلب خلال {days} أيام عمل.")
                bad = (f"The fee for {en} is SAR {fee + 15} and the request is completed within {days + 2} working days." if lang == "en"
                       else f"رسوم {ar} هي {fee + 15} ريالا ويكتمل الطلب خلال {days + 2} أيام عمل.")
                must = [f"{fee} ", f"{days} "]
            tasks["anis"].append({"id": tid, "app": "anis", "lang": lang, "context": sheet, "question": q,
                                  "expected": {"must_include": must, "lang": lang}, "_good": good, "_bad": bad, "_hard": rng.random()})
    for lang in ("en", "ar"):
        for i in range(50):
            reason, resolution, follow = REASONS[i % 6], RESOLUTIONS[(i // 6) % 4], bool(i % 3 == 0)
            said = {"billing": "a charge on the bill", "coverage": "weak signal at home", "roaming": "a roaming pack abroad",
                    "fibre_fault": "the fibre line being down", "plan_change": "moving to another plan", "sim": "a SIM that stopped working"}[reason]
            end = {"resolved": "The agent fixed it during the call.", "callback": "The agent promised to call back.",
                   "escalated": "The agent passed the case to the second line.", "refund_issued": "The agent issued a refund."}[resolution]
            t = (f"[{'Arabic' if lang == 'ar' else 'English'} call, {4 + i % 9} minutes] The customer called about {said}. {end} "
                 f"{'A follow-up was agreed.' if follow else 'No follow-up is needed.'}")
            tasks["khulasa"].append({"id": f"K-{lang}-{i + 1:02d}", "app": "khulasa", "lang": lang, "transcript": t,
                                     "expected": {"reason": reason, "resolution": resolution, "follow_up": follow}, "_hard": rng.random()})
    for lang in ("en", "ar"):
        for i in range(50):
            name, price, _ = PLANS[i % 4]
            kind = ["double_charge", "roaming_no_pack", "late_fee_wrong", "valid_charge", "over_limit"][i % 5]
            charged = {"double_charge": price * 2, "roaming_no_pack": price + 180 + i, "late_fee_wrong": price + 10,
                       "valid_charge": price + 15, "over_limit": price + 640 + 3 * i}[kind]
            decision, refund = {"double_charge": ("refund", price), "roaming_no_pack": ("reject", 0), "late_fee_wrong": ("refund", 10),
                                "valid_charge": ("reject", 0), "over_limit": ("escalate", 0)}[kind]
            case = (f"Plan {name} (SAR {price}). Billed SAR {charged}. Case type on file: {kind.replace('_', ' ')}. "
                    f"Refunds above SAR 500 go to a human.")
            tasks["fasil"].append({"id": f"F-{lang}-{i + 1:02d}", "app": "fasil", "lang": lang, "case": case,
                                   "expected": {"decision": decision, "refund_sar": refund}, "_hard": rng.random()})
    return tasks


def gen_outputs(p, tasks):
    rng = random.Random(p["seed"] + 2)
    rows = []
    shape = {"anis": (7600, 0, 160, 650, 1), "khulasa": (10200, 1024, 330, 750, 1), "fasil": (9400, 7200, 285, 1750, 6)}
    for app in ("anis", "khulasa", "fasil"):
        for lang in ("en", "ar"):
            ts = sorted([t for t in tasks[app] if t["lang"] == lang], key=lambda t: -t["_hard"])   # hardest first
            for (tier, reasoning) in CONFIGS:
                passes = QUOTA[app][(tier, reasoning)][0 if lang == "en" else 1]
                n_fail = 50 - passes
                for rank, t in enumerate(ts):
                    ok = rank >= n_fail
                    status, text = "ok", ""
                    exp = t["expected"]
                    # which failures can be seen without a label: the easier ones (hedges, wrong language, broken JSON, errors)
                    silent = rank < {"en": 2, "ar": 8}[lang] if app == "anis" else rank < max(1, n_fail // 2)
                    if app == "anis":
                        if ok:
                            text = t["_good"]
                        elif silent:
                            text = t["_bad"]
                        else:
                            kind = (rank + (1 if lang == "en" else 0)) % 3
                            if kind == 0:
                                status, text = "error", ""
                            elif kind == 1 or lang == "en":
                                text = ("I am not sure. Please check the plan sheet." if lang == "en" else "لست متأكدا. يرجى مراجعة ورقة الباقات.")
                            else:
                                text = "The plan details are on the plan sheet; the fee is listed there."   # English answer to an Arabic question
                    elif app == "khulasa":
                        good = json.dumps(exp, ensure_ascii=False)
                        if ok:
                            text = good
                        elif silent:
                            wrong = dict(exp, resolution=RESOLUTIONS[(RESOLUTIONS.index(exp["resolution"]) + 1) % 4])
                            text = json.dumps(wrong, ensure_ascii=False)
                        else:
                            text = good[:-12]          # cut off: not valid JSON
                    else:
                        if ok:
                            text = json.dumps(exp)
                        elif silent:
                            wrong = {"decision": "refund" if exp["decision"] != "refund" else "reject", "refund_sar": 25 if exp["decision"] != "refund" else 0}
                            text = json.dumps(wrong)
                        else:
                            text = json.dumps({"decision": "refund", "refund_sar": 4000}) if rank % 2 else '{"decision": "refund", "refund'
                    n_in, cached, n_out, reason, steps = shape[app]
                    k = rng.uniform(0.8, 1.25)
                    n_in, n_out = int(n_in * k), int(n_out * rng.uniform(0.8, 1.25) * (1.2 if lang == "ar" else 1.0))
                    cached = int(cached * k) // 128 * 128 if app == "fasil" else cached
                    reason = int(reason * rng.uniform(0.6, 1.4)) if reasoning == "high" else 0
                    if app == "fasil":
                        n_in, cached, n_out, reason = n_in * steps, cached * steps, n_out * steps, reason * steps
                    if status == "error":
                        n_out = reason = 0
                    per_out = {"tier-s": 4, "tier-m": 7, "tier-l": 11, "local-os": 16}[tier]
                    base = {"tier-s": 350, "tier-m": 500, "tier-l": 800, "local-os": 1500}[tier] * steps
                    lat = int(base + per_out * (n_out + reason) * rng.uniform(0.85, 1.2)) if status == "ok" else rng.randrange(150, 900)
                    rows.append({"app": app, "task": t["id"], "lang": lang, "tier": tier, "reasoning": reasoning, "status": status, "text": text,
                                 "input_tokens": n_in, "cached_tokens": cached, "output_tokens": n_out, "reasoning_tokens": reason, "latency_ms": lat})
    return rows


# --------------------------------------------------------------------------------------------
# Prompt parts and replayed traffic for the caches
# --------------------------------------------------------------------------------------------
def policy_sections():
    out = {}
    for pid, en, ar, fee, days in TOPICS:
        body = [
            f"## {pid} {en} / {ar}",
            f"This section covers {en} for mobile and fibre customers of Mawj. The fee for {en} is SAR {fee}, added to the next bill. "
            f"A request for {en} is completed within {days} working days from the confirmation by one-time code. "
            f"The agent or the assistant states the fee before the customer confirms, and never applies {en} without that confirmation. "
            f"When the customer disputes the fee for {en}, open a bill dispute under P-12 and do not promise a refund. "
            f"Business accounts follow their contract when it differs from this section on {en}.",
            f"يغطي هذا القسم {ar} لعملاء الجوال والألياف في موج. رسوم {ar} هي {fee} ريالا تضاف إلى الفاتورة القادمة. "
            f"يكتمل طلب {ar} خلال {days} أيام عمل من التأكيد برمز التحقق. "
            f"يذكر الموظف أو المساعد الرسوم قبل تأكيد العميل ولا ينفذ {ar} دون هذا التأكيد. "
            f"إذا اعترض العميل على رسوم {ar} يفتح اعتراض على الفاتورة حسب القسم P-12 دون وعد بالاسترداد.",
        ]
        out[pid] = "\n".join(body)
    return out


def instructions_text():
    lines = ["# Anis: instructions (version 7)",
             "You are Anis, the care assistant of Mawj Telecom, a fictional operator. Answer in the language of the customer's last message.",
             "Use only the policy sections and the plan sheet below. When the answer is not there, say so and offer a human agent.",
             "Never state another customer's data. Never promise a refund. Quote fees in SAR with Western digits.",
             "Keep answers under 120 words. Name the policy section you used at the end of the answer.", "", "## Plan sheet"]
    for name, price, allowance in PLANS:
        lines.append(f"- {name}: SAR {price} a month, {allowance}. باقة {name}: {price} ريالا في الشهر.")
    lines.append("")
    lines.append("## Rules by topic")
    for pid, en, ar, fee, days in TOPICS:
        lines.append(f"- For questions about {en} ({ar}), use section {pid}, state the fee of SAR {fee} and the {days} working days, "
                     f"and ask for the one-time code before any change.")
    return "\n".join(lines)


def gen_replay(p):
    rng = random.Random(p["seed"] + 3)
    start = datetime.fromisoformat(p["month_start"]) + timedelta(days=13, hours=19)
    reqs = []
    ids = [t[0] for t in TOPICS]
    sessions = []
    t = 0.0
    while t < 7200:                                   # two busy evening hours
        t += rng.expovariate(1 / 6.5)
        sessions.append(t)
    for s, t0 in enumerate(sessions):
        cust = f"c{rng.randrange(60000):05d}"
        lang = "ar" if rng.random() < 0.62 else "en"
        plan = rng.choice(PLANS)[0]
        profile = f"Customer {cust}. Plan: {plan}. Language: {lang}. Segment: {rng.choice(['consumer', 'family', 'business'])}. Open tickets: {rng.randrange(3)}."
        turns, t, hist = 1, t0, []
        while turns < 6 and rng.random() < 0.52:
            turns += 1
        for k in range(1, turns + 1):
            pid, en, ar, fee, days = rng.choice(TOPICS)
            q = (f"What is the fee for {en} and how long does it take?" if lang == "en" else f"كم رسوم {ar} وكم يستغرق الطلب؟")
            a = (f"The fee for {en} is SAR {fee} and it takes {days} working days. (section {pid})" if lang == "en"
                 else f"رسوم {ar} هي {fee} ريالا ويستغرق {days} أيام عمل. (القسم {pid})")
            order = ids[:]
            rng.shuffle(order)                          # the application builds the pack from a set: the order changes per request
            when = start + timedelta(seconds=t)
            reqs.append({"t": round(t, 1), "session": f"s{s:05d}", "turn": k, "customer": cust, "lang": lang,
                         "clock": when.strftime("%Y-%m-%d %H:%M:%S"), "profile": profile, "section_order": order,
                         "history": list(hist), "question": q, "output_tokens": rng.randrange(90, 240)})
            hist += [q, a]
            t += rng.uniform(25, 95)
    reqs.sort(key=lambda r: r["t"])
    # a quiet stretch after the peak: one session every eight minutes or so, for the stretch task
    quiet, t = [], 7200.0
    for s in range(45):
        t += rng.uniform(240, 720)
        pid, en, ar, fee, days = rng.choice(TOPICS)
        cust = f"c{rng.randrange(60000):05d}"
        when = start + timedelta(seconds=t)
        quiet.append({"t": round(t, 1), "session": f"q{s:05d}", "turn": 1, "customer": cust, "lang": "en",
                      "clock": when.strftime("%Y-%m-%d %H:%M:%S"), "profile": f"Customer {cust}. Plan: Mawj 85. Language: en. Segment: consumer. Open tickets: 0.",
                      "section_order": rng.sample(ids, len(ids)), "history": [], "question": f"What is the fee for {en} and how long does it take?",
                      "output_tokens": rng.randrange(90, 240)})
    return reqs, quiet


def gen_queries(p):
    """Questions to the care assistant over the month, each with the id of its right answer.

    Three kinds: questions about the customer's own account (the answer is that customer's alone),
    frequent general questions (asked again and again in a few wordings, with near-misses such as
    two plans or activate and deactivate), and a long tail of fault reports.
    """
    rng = random.Random(p["seed"] + 4)
    general = []       # (answer_key, [en templates], [ar templates], weight)
    for name, price, allowance in PLANS:
        general.append((f"price:{name}", [f"How much is the {name} plan?", f"What is the monthly price of the {name} plan?", f"price of {name} per month please"],
                        [f"كم سعر باقة {name}؟", f"ما هو السعر الشهري لباقة {name}؟", f"سعر باقة {name} في الشهر لو سمحت"], 0.5))
    for en, ar in SERVICES:
        general.append((f"activate:{en}", [f"How do I activate {en}?", f"How can I turn on {en}?", f"I want to activate {en}"],
                        [f"كيف أفعّل {ar}؟", f"أريد تفعيل {ar}"], 0.6))
        general.append((f"deactivate:{en}", [f"How do I deactivate {en}?", f"How can I turn off {en}?", f"I want to deactivate {en}"],
                        [f"كيف ألغي تفعيل {ar}؟", f"أريد إلغاء تفعيل {ar}"], 0.3))
    for pid, en, ar, fee, days in TOPICS:
        general.append((f"fee:{pid}", [f"What is the fee for {en}?", f"How much does {en} cost?", f"Is there a charge for {en}?"],
                        [f"كم رسوم {ar}؟", f"ما تكلفة {ar}؟", f"هل توجد رسوم على {ar}؟"], 1.0))
        general.append((f"time:{pid}", [f"How long does {en} take?", f"How many days for {en}?"],
                        [f"كم يستغرق {ar}؟", f"كم يوما يحتاج {ar}؟"], 0.7))
    personal = [("balance", ["What is my current balance?", "How much do I owe right now?", "my balance please"], ["كم رصيدي الحالي؟", "كم المبلغ المستحق علي الآن؟"]),
                ("data_left", ["How much data do I have left?", "What is my remaining data?"], ["كم بقي من بياناتي؟", "ما المتبقي من باقة البيانات؟"]),
                ("bill_due", ["When is my bill due?", "What is the due date of my bill?"], ["متى موعد سداد فاتورتي؟", "ما تاريخ استحقاق فاتورتي؟"]),
                ("my_plan", ["Which plan am I on?", "What is my current plan?"], ["ما هي باقتي الحالية؟", "على أي باقة أنا؟"]),
                ("bill_higher", ["Why is my bill higher this month?", "Why did my bill go up this month?"], ["لماذا فاتورتي أعلى هذا الشهر؟", "لماذا ارتفعت فاتورتي هذا الشهر؟"])]
    tail_en = (["router", "phone", "SIM", "modem", "tablet", "smart watch", "landline", "TV box"],
               ["no signal", "slow internet", "dropped calls", "a red light", "no data", "error code 31", "error code 47", "echo on calls", "overheating", "random restarts"],
               ["this morning", "yesterday", "two days ago", "last week", "the storm", "the update", "moving house", "a trip abroad"],
               ["Abha", "Taif", "Jazan", "Najran", "Al-Baha", "Tabuk", "Hail", "Arar", "Yanbu", "Bisha"],
               ["My {d} has {s} since {w} in {p}, what should I do?", "Since {w} my {d} in {p} shows {s}. Any fix?", "{d} problem in {p}: {s} after {w}"])
    tail_ar = (["الراوتر", "الجوال", "الشريحة", "المودم", "الجهاز اللوحي", "الساعة الذكية", "الهاتف الثابت", "جهاز التلفزيون"],
               ["لا توجد إشارة", "الإنترنت بطيء", "المكالمات تنقطع", "ضوء أحمر", "لا توجد بيانات", "رمز الخطأ 31", "رمز الخطأ 47", "صدى في المكالمات", "حرارة مرتفعة", "إعادة تشغيل متكررة"],
               ["منذ الصباح", "منذ أمس", "منذ يومين", "منذ أسبوع", "بعد العاصفة", "بعد التحديث", "بعد الانتقال", "بعد السفر"],
               ["أبها", "الطائف", "جازان", "نجران", "الباحة", "تبوك", "حائل", "عرعر", "ينبع", "بيشة"],
               ["{d} عندي فيه مشكلة: {s} {w} في {p}، ما الحل؟", "{w} و{d} في {p}: {s}. ماذا أفعل؟"])
    order = list(range(len(general)))
    rng.shuffle(order)
    weights = [general[i][3] / (rank + 1) ** 0.35 for rank, i in enumerate(order)]
    custs = [f"c{rng.randrange(60000):05d}" for _ in range(500)]
    rows = []
    for n in range(2400):
        day = 1 + n * p["days"] // 2400
        cust = rng.choice(custs)
        lang = "ar" if rng.random() < 0.6 else "en"
        r = rng.random()
        if r < 0.22:
            key, en, ar = rng.choice(personal)
            text = rng.choice(ar if lang == "ar" else en)
            rows.append({"n": n, "day": day, "customer": cust, "lang": lang, "kind": "personal", "text": text,
                         "answer_key": f"{key}|{cust}", "used_customer_data": True})
        elif r < 0.62:
            key, en, ar, _ = general[order[pick_weighted(rng, weights)]]
            text = rng.choice(ar if lang == "ar" else en)
            if lang == "en" and rng.random() < 0.3:
                text = rng.choice(["Hi, ", "Hello, ", "Please, ", "Quick question: "]) + text[0].lower() + text[1:]
            version = "v2" if (key == "price:Mawj 85" and day >= 15) else "v1"       # the price of one plan changes on day 15
            rows.append({"n": n, "day": day, "customer": cust, "lang": lang, "kind": "general", "text": text,
                         "answer_key": f"{key}|{version}|{lang}", "used_customer_data": False})
        else:
            devices, symptoms, whens, places, templates = tail_ar if lang == "ar" else tail_en
            d, sy = rng.randrange(len(devices)), rng.randrange(len(symptoms))
            text = rng.choice(templates).format(d=devices[d], s=symptoms[sy], w=rng.choice(whens), p=rng.choice(places))
            rows.append({"n": n, "day": day, "customer": cust, "lang": lang, "kind": "fault", "text": text[0].upper() + text[1:],
                         "answer_key": f"fault:{d}:{sy}|{lang}", "used_customer_data": False})
    return rows


# --------------------------------------------------------------------------------------------
# Hosting, batch, outcomes
# --------------------------------------------------------------------------------------------
def gen_hosting(p):
    rng = random.Random(p["seed"] + 5)
    bench = [(1, 5.5, 11.0), (2, 10.6, 11.5), (4, 20.0, 12.5), (8, 36.0, 14.0), (16, 60.0, 17.0), (32, 84.0, 26.0), (64, 96.0, 48.0)]
    price_sheets = {
        "synthetic": True, "currency": "SAR",
        "node": {"model": "local-os", "description": "one accelerator node in an in-Kingdom cloud region, an open-weight model of about 30 billion parameters",
                 "on_demand_per_hour": 14.0, "minimum_lease_hours": 1, "reserved_per_month": 6200.0, "hours_per_month": 744},
        "operations": {"share_of_an_engineer_per_month": 2500.0, "note": "patching, monitoring and on-call for a self-hosted model"},
        "api_regions": {"global": {"multiplier": 1.0, "location": "outside the Kingdom"},
                        "in-kingdom": {"multiplier": PRICES["in_kingdom_premium"], "location": "inside the Kingdom"}},
        "latency_objective": {"interactive_p95_seconds": 20.0, "batch": "none"},
    }
    register = [
        ["DS-01", "anis", "plan sheet and policy sections", "Public", "no", "any region", "not needed"],
        ["DS-02", "anis", "customer profile line and chat history", "Restricted", "yes", "in-Kingdom, or outside with an approved transfer assessment", "approved 2026-09-14"],
        ["DS-03", "khulasa", "call transcripts", "Restricted", "yes", "in-Kingdom, or outside with an approved transfer assessment", "not approved"],
        ["DS-04", "fasil", "itemised bills and payment records", "Restricted", "yes", "in-Kingdom, or outside with an approved transfer assessment", "not approved"],
        ["DS-05", "fasil", "dispute decisions and refunds", "Restricted", "yes", "in-Kingdom only", "not applicable"],
        ["DS-06", "all", "gateway usage log (no prompt text)", "Restricted", "no", "in-Kingdom only", "not applicable"],
    ]
    draws = sorted(round(min(1440.0, rng.lognormvariate(3.65, 0.95)), 1) for _ in range(400))
    batch = {"synthetic": True, "discount": PRICES["batch_discount"], "limit_hours": 24,
             "note": "minutes from submitting a batch to its results, 400 draws; the tier promises 24 hours, most batches take about an hour",
             "completion_minutes": draws}
    energy = {"synthetic": True, "note": "assumed figures for the labs; replace them with the provider's or with a measurement",
              "wh_per_1k_tokens": {"tier-s": {"input": 0.010, "output": 0.10}, "tier-m": {"input": 0.035, "output": 0.35},
                                   "tier-l": {"input": 0.12, "output": 1.20}}, "cached_input_factor": 0.1,
              "local": {"node_kw": 1.4, "overhead_factor": 1.3}}
    human = {"synthetic": True, "currency": "SAR", "escalation_to_a_human": 21.0, "rework_of_a_wrong_resolution": 55.0,
             "floor": {"max_wrong_share_of_resolved": 0.06, "set_by": "the head of billing operations"}}
    return bench, price_sheets, register, batch, energy, human


def gen_outcomes(p, fasil):
    rng = random.Random(p["seed"] + 6)
    rows = []
    for sess, config, kind, day, lang in fasil:
        if rng.random() < 0.04:
            continue                                     # never reviewed: no outcome row
        if kind == "loop":
            outcome = rng.choices(["escalated", "abandoned"], [0.8, 0.2])[0]
        elif config == "A":
            outcome = rng.choices(["resolved_correct", "resolved_wrong", "escalated", "abandoned"], [0.80, 0.04, 0.13, 0.03])[0]
        else:
            outcome = rng.choices(["resolved_correct", "resolved_wrong", "escalated", "abandoned"], [0.64, 0.07, 0.25, 0.04])[0]
        rows.append([sess, config, outcome, rng.randrange(10, 900)])
    for i in range(60):                                  # outcomes of staging sessions that are not in the production log
        rows.append([f"fz{i:05d}", "A", "resolved_correct", rng.randrange(10, 900)])
    rng.shuffle(rows)
    return rows


# --------------------------------------------------------------------------------------------
def build(out: Path, **overrides):
    p = dict(DEFAULTS, **overrides)
    files = {}
    usage, calls, fasil = gen_usage(p)
    files["usage.csv.gz"] = ("gz", csv_text(USAGE_COLS, usage))
    files["prices.json"] = ("text", json.dumps(PRICES, indent=1, ensure_ascii=False) + "\n")
    files["invoice.csv"] = ("text", csv_text(["line", "provider_key", "item", "model", "quantity", "unit", "unit_price_sar", "amount_sar"], gen_invoice(p, usage)))
    files["gpu_hours.csv"] = ("text", csv_text(["date", "hour", "leased", "busy_minutes", "requests", "input_tokens", "output_tokens"], gen_gpu_hours(p, usage)))
    files["gateway/keys.csv"] = ("text", csv_text(["key_id", "team", "app", "env", "owner", "note"], KEYS))
    files["gateway/teams.csv"] = ("text", csv_text(["team", "cost_centre", "owner"], TEAMS))
    day = f"{p['month_start'][:8]}{p['incident_day']:02d}"
    files["gateway/replay_incident_day.csv.gz"] = ("gz", csv_text(USAGE_COLS, [r for r in usage if r[1].startswith(day)]))
    calm = f"{p['month_start'][:8]}{p['incident_day'] - 3:02d}"
    files["gateway/replay_calm_day.csv.gz"] = ("gz", csv_text(USAGE_COLS, [r for r in usage if r[1].startswith(calm)]))
    start_policy = {"note": "Maabar's policy on 1 October: one budget for the whole gateway", "window": "day",
                    "budgets": [{"scope": "gateway", "match": "*", "soft_sar": 208.0, "hard_sar": 260.0}], "rate_limits": []}
    files["gateway/policy_start.json"] = ("text", json.dumps(start_policy, indent=1) + "\n")
    tasks = gen_tasks(p)
    outputs = gen_outputs(p, tasks)
    for app, ts in tasks.items():
        files[f"eval/tasks_{app}.jsonl"] = ("text", jsonl([{k: v for k, v in t.items() if not k.startswith("_")} for t in ts]))
    files["eval/outputs.jsonl.gz"] = ("gz", jsonl(outputs))
    files["eval/floors.json"] = ("text", json.dumps({"note": "lowest acceptable pass rate, in each language", **FLOORS}, indent=1) + "\n")
    reqs, quiet = gen_replay(p)
    files["prompts/anis_instructions.md"] = ("text", instructions_text() + "\n")
    files["prompts/policy_sections.json"] = ("text", json.dumps(policy_sections(), ensure_ascii=False, indent=1) + "\n")
    files["prompts/anis_replay.jsonl.gz"] = ("gz", jsonl(reqs))
    files["prompts/anis_replay_quiet.jsonl"] = ("text", jsonl(quiet))
    files["cache/anis_queries.jsonl"] = ("text", jsonl(gen_queries(p)))
    bench, sheets, register, batch, energy, human = gen_hosting(p)
    files["hosting/throughput_benchmark.csv"] = ("text", csv_text(["concurrency", "requests_per_min", "p95_latency_s"], bench))
    files["hosting/price_sheets.json"] = ("text", json.dumps(sheets, indent=1) + "\n")
    files["hosting/classification_register.csv"] = ("text", csv_text(["dataset", "application", "content", "classification", "personal_data", "placement_rule", "transfer_assessment"], register))
    files["hosting/batch_tier.json"] = ("text", json.dumps(batch) + "\n")
    files["hosting/energy.json"] = ("text", json.dumps(energy, indent=1) + "\n")
    files["hosting/khulasa_calls.csv"] = ("text", csv_text(["request_id", "session_id", "urgent", "call_minutes"], calls))
    files["outcomes/disputes.csv"] = ("text", csv_text(["session_id", "config", "outcome", "disputed_sar"], gen_outcomes(p, fasil)))
    files["outcomes/human_cost.json"] = ("text", json.dumps(human, indent=1) + "\n")
    if out is None:
        return files
    for name, (kind, text) in files.items():
        (writer_gz if kind == "gz" else write_text)(out / name, text)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "data"))
    ap.add_argument("--check", action="store_true", help="compare a fresh build with the files on disk")
    a = ap.parse_args()
    if a.check:
        files, bad = build(None), []
        for name, (kind, text) in files.items():
            path = Path(a.out) / name
            have = (gzip.decompress(path.read_bytes()) if kind == "gz" else path.read_bytes()) if path.exists() else b""
            if have != text.encode("utf-8"):
                bad.append(name)
        print("data matches the generator" if not bad else f"differs: {bad}")
        raise SystemExit(1 if bad else 0)
    files = build(Path(a.out))
    print(f"wrote {len(files)} files to {a.out}")


if __name__ == "__main__":
    main()
