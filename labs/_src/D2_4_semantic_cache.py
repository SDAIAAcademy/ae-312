# %% [markdown]
# # Lab 2.4 · A semantic cache and its wrong answers
#
# Day 2 · Session 4 (Semantic caches and their risks) · 25 min.
#
# A response cache answers a question with an answer it gave before, and skips the model. An exact cache needs the
# same words; a semantic cache accepts a question that is close enough. You measure what "close enough" serves: hit
# rate, wrong answers, and answers that belong to another customer. Then you scope the cache and write the test that
# proves no answer crosses customers.
#
# **AI policy: tutor.** An assistant may explain numpy syntax. The scope rule and the test are yours.
#
# **Reference state.** `data/cache/anis_queries.jsonl`: 2,400 questions to the care assistant over the month, each
# with the id of its right answer (`answer_key`), the customer, and `used_customer_data`, which the application
# knows when it writes an answer: did producing it read the customer's account? `M.embed` is a small local
# embedding (hashed character 3-grams): no model, no key. No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · An exact-match cache as the baseline (4')
# - [ ] 2 · A semantic cache at three thresholds (7')
# - [ ] 3 · The wrong-answer rate from labelled questions (6')
# - [ ] 4 · An isolation test: failing, then passing (8')
# - [ ] ✱ Stretch · A price changes on day 15: how long does the cache serve the old one?

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-312.git"
    if not Path("/content/ae-312").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-312"], check=True)
    os.chdir("/content/ae-312/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("mawj.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import re

import numpy as np
import pandas as pd

import mawj as M

# %%
Q = M.read_jsonl(M.DATA / "cache" / "anis_queries.jsonl")
E = M.embed([q["text"] for q in Q])
print(pd.Series([q["kind"] for q in Q]).value_counts().to_string())
for i in (3, 4, 7, 12):
    print(f"  day {Q[i]['day']:2d} {Q[i]['customer']} [{Q[i]['kind']}] {Q[i]['text']}  ->  {Q[i]['answer_key']}")


def run_cache(find, scope=lambda q: "all"):
    """Serve the 2,400 questions in order through a cache. One row per question.

    find(i, entries) returns the index of the cached question whose answer is served, or None for a miss.
    scope(q) names the partition of the cache a question may read and write.
    """
    store, rows = {}, []
    for i, q in enumerate(Q):
        entries = store.setdefault(scope(q), [])
        j = find(i, entries) if entries else None
        if j is None:
            entries.append(i)                      # a miss: the model answers, the answer is stored
            rows.append({"n": i, "hit": False, "served_from": -1, "wrong": False, "crossed": False})
        else:
            rows.append({"n": i, "hit": True, "served_from": j, "wrong": Q[j]["answer_key"] != q["answer_key"],
                         "crossed": bool(Q[j]["used_customer_data"] and Q[j]["customer"] != q["customer"])})
    return pd.DataFrame(rows)


# %% [markdown]
# ## 1 · An exact-match cache as the baseline (4')
#
# ✏️ **Exercise** · Write `normalise(text)`: lower case, punctuation removed, runs of spaces collapsed. Two
# questions with the same normalised text share a cache entry.

# %%
def normalise(text):
    # BEGIN SOLUTION
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    NORM = [normalise(q["text"]) for q in Q]
except NotImplementedError:
    NORM = [re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", q["text"].lower())).strip() for q in Q]


def find_exact(i, entries):
    return next((j for j in entries if NORM[j] == NORM[i]), None)


exact = run_cache(find_exact)
print(f"exact cache: hit rate {exact.hit.mean():.1%} | wrong answers served {int(exact.wrong.sum())} | of them another customer's {int(exact.crossed.sum())}")
M.check(exact.crossed.sum() > 0, "even an exact cache serves one customer's answer to another: \"what is my balance\" is the same text for everyone")

# %% [markdown]
# ## 2 · A semantic cache at three thresholds (7')
#
# The rows of `E` are unit vectors, so the dot product of two rows is their cosine similarity.
#
# ✏️ **Exercise** · Write `nearest(i, entries, threshold)`: among the cached questions `entries` (a list of
# indices), return the index of the one most similar to question `i` when its similarity is at least `threshold`,
# and `None` otherwise.

# %%
def nearest(i, entries, threshold):
    # BEGIN SOLUTION
    sims = E[entries] @ E[i]
    k = int(np.argmax(sims))
    return entries[k] if sims[k] >= threshold else None
    # END SOLUTION


# %%
def _nearest(i, entries, threshold):
    try:
        return nearest(i, entries, threshold)
    except NotImplementedError:
        sims = E[entries] @ E[i]
        k = int(np.argmax(sims))
        return entries[k] if sims[k] >= threshold else None


THRESHOLDS = [0.80, 0.90, 0.95]
runs = {th: run_cache(lambda i, entries, th=th: _nearest(i, entries, th)) for th in THRESHOLDS}
for th, r in runs.items():
    print(f"threshold {th:.2f}: hit rate {r.hit.mean():.1%}")
example = runs[0.80][runs[0.80].wrong & ~runs[0.80].crossed].iloc[0]
print(f"\none wrong hit at 0.80:\n  asked:  {Q[int(example.n)]['text']}\n  served: the answer to \"{Q[int(example.served_from)]['text']}\"")
M.check(runs[0.80].hit.mean() > runs[0.90].hit.mean() > runs[0.95].hit.mean() > exact.hit.mean(), "a lower threshold answers more questions from the cache")

# %% [markdown]
# ## 3 · The wrong-answer rate (6')
#
# A hit rate is half of a measurement. The questions are labelled: a hit is **wrong** when the cached answer's
# `answer_key` differs from the question's.
#
# ✏️ **Exercise** · Write `rates(r)` returning a dictionary: `hit_rate`, `wrong_rate` (wrong answers over **all**
# questions), `wrong_of_hits` (wrong answers over hits) and `crossed` (answers that belong to another customer).

# %%
def rates(r):
    # BEGIN SOLUTION
    return {"hit_rate": float(r.hit.mean()), "wrong_rate": float(r.wrong.mean()),
            "wrong_of_hits": float(r.wrong.sum() / max(1, r.hit.sum())), "crossed": int(r.crossed.sum())}
    # END SOLUTION


# %%
def _rates(r):
    try:
        return rates(r)
    except NotImplementedError:
        return {"hit_rate": float(r.hit.mean()), "wrong_rate": float(r.wrong.mean()),
                "wrong_of_hits": float(r.wrong.sum() / max(1, r.hit.sum())), "crossed": int(r.crossed.sum())}


naive = pd.DataFrame({"exact": _rates(exact), **{f"semantic {th:.2f}": _rates(r) for th, r in runs.items()}}).T
M.keep("d2_4_naive", naive.rename_axis("cache").reset_index())
print(naive.round(3).to_string())
M.check(naive.crossed.min() > 400, "at every threshold several hundred answers went to the wrong customer: a threshold does not fix that")

# %% [markdown]
# 🔍 Raising the threshold removes wrong answers about plans and faults. The number in `crossed` hardly moves:
# "what is my balance" asked by two customers is the **same** question, at similarity 1. Isolation is not a
# matter of similarity.

# %% [markdown]
# ## 4 · An isolation test: failing, then passing (8')
#
# The application knows, when it stores an answer, whether producing it read the customer's account
# (`used_customer_data`). Such an answer may only ever be served to the same customer.
#
# ✏️ **Exercise** · Write `scope_of(q)`: the name of the cache partition for a question: one shared partition for
# answers that used no customer data, and one partition per customer for those that did. Then write
# `test_no_answer_crosses_customers(r)`, which raises `AssertionError` when any served answer crossed.

# %%
def scope_of(q):
    # BEGIN SOLUTION
    return f"customer:{q['customer']}" if q["used_customer_data"] else "public"
    # END SOLUTION


def test_no_answer_crosses_customers(r):
    # BEGIN SOLUTION
    assert int(r.crossed.sum()) == 0, f"{int(r.crossed.sum())} answers were served to another customer"
    # END SOLUTION


# %%
def _scope(q):
    try:
        return scope_of(q)
    except NotImplementedError:
        return f"customer:{q['customer']}" if q["used_customer_data"] else "public"


def _test(r):
    try:
        test_no_answer_crosses_customers(r)
    except NotImplementedError:
        assert int(r.crossed.sum()) == 0, f"{int(r.crossed.sum())} answers were served to another customer"


try:
    _test(runs[0.95])
    failed_first = False
except AssertionError as e:
    failed_first = True
    print("the test on the unscoped cache fails, as it must:", e)

scoped_runs = {th: run_cache(lambda i, entries, th=th: _nearest(i, entries, th), scope=_scope) for th in THRESHOLDS}
for r in scoped_runs.values():
    _test(r)
scoped = pd.DataFrame({f"scoped {th:.2f}": _rates(r) for th, r in scoped_runs.items()}).T
print(scoped.round(3).to_string())
ok = scoped[scoped.wrong_rate <= 0.01]
chosen = ok.sort_values("hit_rate", ascending=False).iloc[0]
anis_month = 911.32
M.keep("d2_4_scoped", scoped.rename_axis("cache").reset_index())
M.keep("d2_4_summary", {"chosen": chosen.name, "hit_rate": round(float(chosen.hit_rate), 4), "wrong_rate": round(float(chosen.wrong_rate), 4),
                        "crossed": int(chosen.crossed), "saving_sar_month": round(anis_month * float(chosen.hit_rate), 2)})
print(f"\nthe isolation test passes at every threshold | with at most 1% wrong answers: {chosen.name}, hit rate {chosen.hit_rate:.1%}, "
      f"about {M.sar(anis_month * chosen.hit_rate)} of Anis's {M.sar(anis_month)} a month")
M.check(failed_first and scoped.crossed.sum() == 0, "the isolation test fails on the unscoped cache and passes on the scoped one")
M.check(scoped.loc["scoped 0.80", "wrong_rate"] > 0.1 > scoped.loc["scoped 0.95", "wrong_rate"], "the threshold still trades hits for wrong answers")

# %% [markdown]
# 🔍 At 0.80 the scoped cache answers more than half of the questions and gets one in five of **all** questions
# wrong. Nobody would ship that if they had measured it. The wrong-answer rate needs labelled questions; the
# isolation test needs none and belongs in the pipeline.

# %% [markdown]
# ## ✱ Stretch · Stale answers
#
# On day 15 the price of one plan changed; the right answers from that day on end in `|v2|`. At threshold 0.95, on
# which days does the scoped cache still serve the old price? Add a lifetime of 3 days to the entries and count
# again. What does the lifetime cost in hit rate?

# %%
def stretch():
    # BEGIN SOLUTION
    r = scoped_runs[0.95]
    stale = [int(x.n) for x in r.itertuples() if x.hit and "|v2|" in Q[int(x.n)]["answer_key"] and "|v1|" in Q[int(x.served_from)]["answer_key"]]
    print(f"old price served {len(stale)} times, on days {sorted({Q[i]['day'] for i in stale})}")

    def fresh(i, entries, days=3):
        recent = [j for j in entries if Q[i]["day"] - Q[j]["day"] <= days]
        return _nearest(i, recent, 0.95) if recent else None

    r2 = run_cache(fresh, scope=_scope)
    stale2 = [int(x.n) for x in r2.itertuples() if x.hit and "|v2|" in Q[int(x.n)]["answer_key"] and "|v1|" in Q[int(x.served_from)]["answer_key"]]
    print(f"with a 3-day lifetime: old price served {len(stale2)} times | hit rate {r2.hit.mean():.1%} against {r.hit.mean():.1%}")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A semantic cache reports a hit rate of 55%. What else do you need before you call it a saving?
#    <details><summary>Answer</summary>The wrong-answer rate on labelled questions at that threshold, and the
#    isolation test. A cache that answers fast and wrong moves the cost to the customer.</details>
# 2. Why does raising the threshold not stop answers from crossing customers?
#    <details><summary>Answer</summary>The same question from two customers has similarity 1. The answers differ
#    because the data differs, not the words. The fix is the scope of the entry.</details>
# 3. Where would you keep the entries?
#    <details><summary>Answer</summary>In a store the team already runs: a key-value store for exact entries, a
#    vector index beside the application's database for semantic ones, with the scope in the key and a lifetime
#    on every entry.</details>
#
# **Carry forward.** The rates of the scoped cache and the passing test are the caching evidence the capstone asks
# for.
