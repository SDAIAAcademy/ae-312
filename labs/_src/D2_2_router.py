# %% [markdown]
# # Lab 2.2 · A two-tier router with a quality check
#
# Day 2 · Session 2 (Routing and cascades) · 25 min.
#
# The medium tier keeps the care assistant's floor and costs five times the small one. Most questions do not need
# it. You build a cascade: try the small tier, check the answer without knowing the right one, escalate to the
# medium tier when the check fails or the call errors. Then you measure what the business pays for: cost per
# successful outcome, with the floor held in Arabic and in English.
#
# **AI policy: tutor.** An assistant may explain syntax. The check and the routing rule are yours.
#
# **Reference state.** `data/eval/tasks_anis.jsonl` and `data/eval/outputs.jsonl.gz` (supplied outputs of both tiers
# for every task; **synthetic**). Routing is replayed on them, so no model is called and no earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · Baselines: always small, always medium (4')
# - [ ] 2 · A quality check that needs no label (6')
# - [ ] 3 · The cascade, with fallback on errors (8')
# - [ ] 4 · Cost per successful outcome, and the router file (7')
# - [ ] ✱ Stretch · What a tier switch in the middle of a session costs in cache

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

import json

import pandas as pd

import mawj as M

# %%
TASKS = {t["id"]: t for t in M.tasks("anis")}
FLOOR = M.load_json("eval/floors.json")["anis"]
outs = M.outputs()
o = M.add_cost(outs[(outs.app == "anis") & (outs.reasoning == "off") & outs.tier.isin(["tier-s", "tier-m"])].rename(columns={"tier": "model"})).rename(columns={"model": "tier"})
o["passed"] = [M.grade("anis", TASKS[r.task], r.text) for r in o.itertuples()]       # the label: known here, unknown in production
OUT = {(r.task, r.tier): r for r in o.itertuples()}
print(o.groupby(["tier", "lang"]).agg(passed=("passed", "sum"), errors=("status", lambda s: int((s == "error").sum())), sar=("cost_sar", "sum")).round(3).to_string())

# %% [markdown]
# ## 1 · Baselines: always small, always medium (4')
#
# The unit is the **successful outcome**: a customer who got a right answer in their language. A failed answer is
# paid for and is not an outcome.
#
# ✏️ **Exercise** · Write `report(rows)` for a frame with one row per task (`lang`, `passed`, `cost_sar`): a
# dictionary with `en` and `ar` (pass rates), `cost_sar` (total for the 100 tasks), `successes` and
# `sar_per_success`.

# %%
def report(rows):
    # BEGIN SOLUTION
    rate = rows.groupby("lang").passed.mean()
    return {"en": float(rate["en"]), "ar": float(rate["ar"]), "cost_sar": float(rows.cost_sar.sum()),
            "successes": int(rows.passed.sum()), "sar_per_success": float(rows.cost_sar.sum() / rows.passed.sum())}
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
def _report(rows):
    try:
        return report(rows)
    except NotImplementedError:
        rate = rows.groupby("lang").passed.mean()
        return {"en": float(rate["en"]), "ar": float(rate["ar"]), "cost_sar": float(rows.cost_sar.sum()),
                "successes": int(rows.passed.sum()), "sar_per_success": float(rows.cost_sar.sum() / rows.passed.sum())}


results = {"always tier-s": _report(o[o.tier == "tier-s"]), "always tier-m": _report(o[o.tier == "tier-m"])}
print(pd.DataFrame(results).T.round(4).to_string())
M.check(results["always tier-s"]["sar_per_success"] < results["always tier-m"]["sar_per_success"] and results["always tier-s"]["ar"] < FLOOR,
        "the small tier is cheapest per success and fails the floor in Arabic: cost per success alone does not choose")

# %% [markdown]
# ## 2 · A quality check that needs no label (6')
#
# In production nobody tells the router whether an answer was right. It can still see four things: the call
# errored; the answer is empty; the answer is not in the language of the question; the answer hedges ("I am not
# sure", "لست متأكدا").
#
# ✏️ **Exercise** · Write `looks_ok(task, row)` from `row.status`, `row.text` and `task["question"]`. It must not
# read `task["expected"]` or `row.passed`.

# %%
HEDGES = ("not sure", "لست متأكدا")


def looks_ok(task, row):
    # BEGIN SOLUTION
    if row.status != "ok" or not row.text:
        return False
    if M.language_of(row.text) != M.language_of(task["question"]):
        return False
    return not any(h in row.text for h in HEDGES)
    # END SOLUTION


# %%
def _looks_ok(task, row):
    try:
        return looks_ok(task, row)
    except NotImplementedError:
        return row.status == "ok" and bool(row.text) and M.language_of(row.text) == M.language_of(task["question"]) and not any(h in row.text for h in HEDGES)


small = o[o.tier == "tier-s"].copy()
small["check_ok"] = [_looks_ok(TASKS[r.task], r) for r in small.itertuples()]
confusion = small.groupby(["lang", "passed", "check_ok"]).size().unstack(fill_value=0)
print(confusion.to_string())
silent = small[~small.passed & small.check_ok].groupby("lang").size()
caught = small[~small.passed & ~small.check_ok].groupby("lang").size()
M.keep("d2_2_check", {"silent_failures": silent.to_dict(), "caught_failures": caught.to_dict(), "false_alarms": int((small.passed & ~small.check_ok).sum())})
print(f"\nfailures the check catches: {caught.to_dict()} | failures it lets through: {silent.to_dict()} | right answers it rejects: {int((small.passed & ~small.check_ok).sum())}")
M.check(silent.get("ar", 0) > silent.get("en", 0), "the check lets through more wrong answers in Arabic than in English")

# %% [markdown]
# 🔍 The failures the check lets through are answers in the right language, confident, with a wrong fee or a wrong
# price. No cheap check sees those. That number, by language, decides what a cascade can promise.

# %% [markdown]
# ## 3 · The cascade, with fallback on errors (8')
#
# A policy is a dictionary: `{"first": "tier-s", "second": "tier-m", "direct": {}}`. `direct` maps a language to
# the tier that receives its requests straight away (empty for now).
#
# ✏️ **Exercise** · Write `route(task, policy)`: answer with the first tier (or the direct tier for the task's
# language); when the answer does not look ok, answer again with the second tier. Return a dictionary with `task`,
# `lang`, `final_tier`, `escalated`, `passed` (of the final answer) and `cost_sar` (**every** attempt is paid).
# `OUT[(task_id, tier)]` is the supplied output of a tier for a task.

# %%
def route(task, policy):
    # BEGIN SOLUTION
    lang = M.language_of(task["question"])
    tier = policy["direct"].get(lang, policy["first"])
    row = OUT[(task["id"], tier)]
    cost, escalated = row.cost_sar, False
    if tier != policy["second"] and not _looks_ok(task, row):
        tier, escalated = policy["second"], True
        row = OUT[(task["id"], tier)]
        cost += row.cost_sar
    return {"task": task["id"], "lang": task["lang"], "final_tier": tier, "escalated": escalated, "passed": bool(row.passed), "cost_sar": cost}
    # END SOLUTION


# %%
CASCADE = {"first": "tier-s", "second": "tier-m", "direct": {}}
try:
    routed = pd.DataFrame([route(t, CASCADE) for t in TASKS.values()])
except NotImplementedError:
    routed = M.reference("d2_2_cascade")
M.keep("d2_2_cascade", routed)
results["cascade s then m"] = _report(routed)
print(routed.groupby("lang").agg(escalated=("escalated", "sum"), passed=("passed", "sum"), sar=("cost_sar", "sum")).round(3).to_string())
print(pd.DataFrame(results).T.round(4).to_string())
M.check(results["cascade s then m"]["en"] >= FLOOR and results["cascade s then m"]["ar"] < FLOOR,
        "the cascade keeps the floor in English and misses it in Arabic")

# %% [markdown]
# 🔍 The cascade is cheap and it fails the floor in the language of most customers. A cheaper route must keep the
# floor in Arabic **and** in English, or it is not an option.

# %% [markdown]
# ## 4 · Cost per successful outcome, and the router file (7')
#
# Step 2 said why: in Arabic the small tier fails in ways the check cannot see. Route by what you measured.
#
# ✏️ **Exercise** · Write `language_policy()` returning a policy that sends Arabic straight to the medium tier and
# keeps the cascade for English.

# %%
def language_policy():
    # BEGIN SOLUTION
    return {"first": "tier-s", "second": "tier-m", "direct": {"ar": "tier-m"}}
    # END SOLUTION


# %%
try:
    POLICY = language_policy()
    routed2 = pd.DataFrame([route(t, POLICY) for t in TASKS.values()])
except NotImplementedError:
    POLICY = {"first": "tier-s", "second": "tier-m", "direct": {"ar": "tier-m"}}
    routed2 = M.reference("d2_2_routed")
M.keep("d2_2_routed", routed2)
results["cascade, Arabic direct to m"] = _report(routed2)
table = pd.DataFrame(results).T
table["meets_floor"] = (table.en >= FLOOR) & (table.ar >= FLOOR)
print(table.round(4).to_string())
base, new = results["always tier-m"], results["cascade, Arabic direct to m"]
saving = 1 - new["sar_per_success"] / base["sar_per_success"]
config = {"application": "anis", "policy": POLICY, "quality_check": ["status ok", "not empty", "language of the question", "no hedge phrase"],
          "floor": FLOOR, "measured_on": "100 labelled tasks, supplied outputs (synthetic)",
          "result": {k: round(v, 5) for k, v in new.items()}, "baseline": {"always": "tier-m", **{k: round(v, 5) for k, v in base.items()}},
          "saving_per_success_pct": round(100 * saving, 1)}
(M.lab_dir("D2_2") / "router.json").write_text(json.dumps(config, indent=1, ensure_ascii=False), encoding="utf-8")
M.keep("d2_2_summary", {"table": table.reset_index().rename(columns={"index": "policy"}), "saving_per_success_pct": round(100 * saving, 1)})
print(f"\ncost per successful outcome: SAR {new['sar_per_success']:.4f} against SAR {base['sar_per_success']:.4f} always on the medium tier: {saving:.0%} less | router file written to artifacts/D2_2/router.json")
M.check(bool(table.loc["cascade, Arabic direct to m", "meets_floor"]) and saving > 0.2, "the router keeps the floor in both languages and costs less per successful outcome")

# %% [markdown]
# 🔍 The saving comes from English alone. If the share of Arabic traffic in production is 62% and not the 50% of the
# task set, what is the saving on the month? Say which mix a number was measured on.

# %% [markdown]
# ## ✱ Stretch · The cache cost of switching tiers
#
# A cache belongs to one model. When turn 3 of a conversation escalates from the small tier to the medium one, the
# medium tier has never seen the prompt. Price one escalated turn of 7,600 input tokens and 160 output tokens on the
# medium tier twice: with 7,424 of its input tokens cached (as after Lab 2.3), and with none.

# %%
def stretch():
    # BEGIN SOLUTION
    p = M.prices()["tiers"]["tier-m"]
    warm = ((7600 - 7424) * p["input"] + 7424 * p["cached_input"] + 160 * p["output"]) / 1e6
    cold = (7600 * p["input"] + 160 * p["output"]) / 1e6
    print(f"escalated turn with a warm cache SAR {warm:.5f} | after a switch SAR {cold:.5f} | the switch costs {cold / warm:.1f} times a warm turn")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A cascade answers 30% of requests twice. Where does the cost of the first, rejected answers go?
#    <details><summary>Answer</summary>Into the cost of the successful outcomes: total spend over successes.
#    A cascade pays when the cheap tier succeeds often enough to cover its own failures.</details>
# 2. Why not escalate every Arabic answer of the small tier that "looks wrong"?
#    <details><summary>Answer</summary>The check cannot see the confident wrong ones, and those are most of the
#    Arabic failures. Routing Arabic directly uses what the evaluation measured.</details>
# 3. What must be re-measured when the provider updates the small tier?
#    <details><summary>Answer</summary>Everything in this lab: pass rates by language, what the check catches, the
#    saving. A router configuration is a result with a date.</details>
#
# **Carry forward.** `artifacts/D2_2/router.json` is the router configuration with its measured saving that the
# capstone asks for.
