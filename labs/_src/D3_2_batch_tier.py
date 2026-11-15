# %% [markdown]
# # Lab 3.2 · The call-summary job on a batch tier
#
# Day 3 · Session 2 (Batch versus interactive) · 25 min.
#
# Khulasa summarises every call the moment it ends, at the interactive price. A supervisor reads most summaries
# the next day. A batch tier costs half and promises results within 24 hours; most batches are back in about an
# hour. You recompute the month on the batch tier, measure turnaround under three submission schedules, keep the
# urgent calls interactive, and decide.
#
# **AI policy: tutor.** An assistant may explain datetime arithmetic. The schedule and the split are yours.
#
# **Reference state.** `data/usage.csv.gz`, `data/hosting/khulasa_calls.csv` (which calls are urgent),
# `data/hosting/batch_tier.json` (the discount and 400 observed completion times; synthetic). Prices are those of
# the in-Kingdom region, as the register requires for call transcripts. No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · What the job costs on the interactive tier (4')
# - [ ] 2 · The same month on the batch tier (5')
# - [ ] 3 · Turnaround under three submission schedules (9')
# - [ ] 4 · Keep the urgent calls interactive, and decide (7')
# - [ ] ✱ Stretch · Stack the batch discount with a cached prefix

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

import numpy as np
import pandas as pd

import mawj as M

# %%
REGION = "in-kingdom"
calls = pd.read_csv(M.DATA / "hosting" / "khulasa_calls.csv")
BATCH = M.load_json("hosting/batch_tier.json")
DRAWS = np.array(BATCH["completion_minutes"])
u = M.usage()
k = u[u.session_id.isin(calls.session_id)].merge(calls[["session_id", "urgent"]], on="session_id")
k = M.add_cost(k, region=REGION)                   # interactive prices, in-Kingdom region
done = k[k.status == "ok"].copy()                  # one successful request per call
NEED_NORMAL_MIN, NEED_URGENT_MIN = 12 * 60, 15     # a summary is needed within 12 hours; an urgent one within 15 minutes
print(f"{len(done):,} calls summarised | {int(done.urgent.sum()):,} urgent ({done.urgent.mean():.1%}) | {len(k) - len(done)} failed attempts")
print(f"batch tier: {BATCH['discount']:.0%} of the price, results within {BATCH['limit_hours']} hours | "
      f"observed completion, minutes: median {np.median(DRAWS):.0f}, 95th percentile {np.percentile(DRAWS, 95):.0f}, longest {DRAWS.max():.0f}")

# %% [markdown]
# ## 1 · What the job costs on the interactive tier (4')
#
# ✏️ **Exercise** · Write `interactive_cost(k)`: a dictionary with `sar_month` (every billed attempt of the month),
# `sar_per_call` (over the calls that were summarised) and `failed_sar` (what the timeouts cost).

# %%
def interactive_cost(k):
    # BEGIN SOLUTION
    return {"sar_month": float(k.cost_sar.sum()), "sar_per_call": float(k.cost_sar.sum() / (k.status == "ok").sum()),
            "failed_sar": float(k[k.status != "ok"].cost_sar.sum())}
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    now = interactive_cost(k)
except NotImplementedError:
    now = M.reference("d3_2_interactive")
M.keep("d3_2_interactive", now)
print({key: round(v, 4) for key, v in now.items()})
M.check(abs(now["sar_month"] - k.cost_sar.sum()) < 0.01, "the interactive month, failed attempts included")

# %% [markdown]
# ## 2 · The same month on the batch tier (5')
#
# In a batch there is no client waiting, so no client timeout: each call is submitted once.
# `M.add_cost(df, region=REGION, batch=True)` applies the batch price.
#
# ✏️ **Exercise** · Write `batch_cost(done)`: the cost in SAR of the month's calls if every one went through the
# batch tier.

# %%
def batch_cost(done):
    # BEGIN SOLUTION
    return float(M.add_cost(done, region=REGION, batch=True).cost_sar.sum())
    # END SOLUTION


# %%
try:
    all_batch = batch_cost(done)
except NotImplementedError:
    all_batch = M.reference("d3_2_all_batch")
M.keep("d3_2_all_batch", all_batch)
print(f"interactive {M.sar(now['sar_month'])} | all on the batch tier {M.sar(all_batch)} | {1 - all_batch / now['sar_month']:.0%} less")
M.check(all_batch < 0.51 * now["sar_month"], "the batch tier halves the price, and the failed attempts disappear")

# %% [markdown]
# ## 3 · Turnaround under three submission schedules (9')
#
# The price is half. The question is when the summary arrives. A call waits for the next submission, then for its
# batch to complete: **turnaround = wait until the batch is submitted + completion time of that batch**.
# `completion_minutes(slot)` gives a completion time for each batch, drawn from the observed ones.
#
# ✏️ **Exercise** · Write `turnaround_minutes(ts, every_hours)`: for calls ending at the times `ts`, with a batch
# submitted every `every_hours` hours from midnight (24 means once a day, at midnight), the minutes from the end of
# each call to its summary.

# %%
def completion_minutes(slot):
    """The completion time of the batch submitted at `slot` (a timestamp): the same batch always gets the same draw."""
    minutes = ((slot - pd.Timestamp("2026-01-01")).dt.total_seconds() // 60).astype("int64")
    return DRAWS[((minutes * 7919) % len(DRAWS)).to_numpy()]


def turnaround_minutes(ts, every_hours):
    # BEGIN SOLUTION
    slot = ts.dt.ceil(f"{every_hours}h")
    wait = (slot - ts).dt.total_seconds() / 60
    return wait + completion_minutes(slot)
    # END SOLUTION


# %%
def _turnaround(ts, every_hours):
    try:
        return turnaround_minutes(ts, every_hours)
    except NotImplementedError:
        slot = ts.dt.ceil(f"{every_hours}h")
        return (slot - ts).dt.total_seconds() / 60 + completion_minutes(slot)


SCHEDULES = {"every hour": 1, "every 4 hours": 4, "once a day": 24}
normal = done[done.urgent == 0]
rows = []
for name, hours in SCHEDULES.items():
    t = _turnaround(normal.ts, hours)
    rows.append({"schedule": name, "median_h": t.median() / 60, "p95_h": t.quantile(0.95) / 60, "longest_h": t.max() / 60,
                 "within_12h": float((t <= NEED_NORMAL_MIN).mean())})
turn = pd.DataFrame(rows)
M.keep("d3_2_turnaround", turn)
print(turn.round(3).to_string(index=False))
M.check(turn.within_12h.iloc[0] > turn.within_12h.iloc[2], "submitting more often brings more summaries in within 12 hours")

# %% [markdown]
# 🔍 "Results within 24 hours" is the provider's promise; "most in about an hour" is an observation. Plan the
# schedule on the distribution and keep an answer ready for the batch that takes five hours.

# %% [markdown]
# ## 4 · Keep the urgent calls interactive, and decide (7')
#
# An escalated call needs its summary within 15 minutes: no batch schedule gives that. Split the workload.
#
# ✏️ **Exercise** · Write `plan(done, every_hours)`: urgent calls stay interactive (their `cost_sar` as it is),
# the others go to the batch tier on the given schedule. Return a dictionary with `sar_month`, `on_time` (the share
# of **all** calls whose summary arrives within its need: 15 minutes for urgent ones, which the interactive tier
# meets, and 12 hours for the others) and `batch_share` (the share of calls on the batch tier).

# %%
def plan(done, every_hours):
    # BEGIN SOLUTION
    urgent, rest = done[done.urgent == 1], done[done.urgent == 0]
    cost = urgent.cost_sar.sum() + M.add_cost(rest, region=REGION, batch=True).cost_sar.sum()
    on_time = (len(urgent) + (_turnaround(rest.ts, every_hours) <= NEED_NORMAL_MIN).sum()) / len(done)
    return {"sar_month": float(cost), "on_time": float(on_time), "batch_share": float(len(rest) / len(done))}
    # END SOLUTION


# %%
try:
    plans = pd.DataFrame({name: plan(done, hours) for name, hours in SCHEDULES.items()}).T
except NotImplementedError:
    plans = M.reference("d3_2_plans").set_index("schedule")
plans["saving_pct"] = 100 * (1 - plans.sar_month / now["sar_month"])
M.keep("d3_2_plans", plans.rename_axis("schedule").reset_index())
print(plans.round(3).to_string())
good = plans[plans.on_time >= 0.99]
decision = good.index[-1] if len(good) else plans.on_time.idxmax()       # the least frequent schedule that is on time for 99%
M.keep("d3_2_summary", {"decision": decision, "sar_month": round(float(plans.loc[decision, "sar_month"]), 2), "interactive_sar_month": round(now["sar_month"], 2),
                        "saving_pct": round(float(plans.loc[decision, "saving_pct"]), 1), "on_time": round(float(plans.loc[decision, "on_time"]), 4)})
print(f"\ndecision: urgent calls interactive, the rest in a batch {decision}: {M.sar(plans.loc[decision, 'sar_month'])} a month "
      f"against {M.sar(now['sar_month'])}, {plans.loc[decision, 'saving_pct']:.0f}% less, {plans.loc[decision, 'on_time']:.1%} of summaries on time")
M.check(plans.loc["once a day", "on_time"] < 0.99 <= plans.loc["every hour", "on_time"], "once a day misses the 12-hour need; every hour meets it for 99% of calls")
M.check(plans.saving_pct.between(35, 50).all(), "with urgent calls kept interactive the saving is below the headline 50%")

# %% [markdown]
# 🔍 The discount is 50%; the saving is less, because 8% of the calls stay at the full price and those are not the
# shortest ones. Whoever reads "50% off" in a price list should see this number instead.

# %% [markdown]
# ## ✱ Stretch · Batch and a cached prefix
#
# Batch and cache discounts can stack. Every request of Khulasa starts with the same 1,100 tokens of instructions,
# of which 1,024 are cacheable. What does the cached prefix add to the batch saving for this job, and why so little?

# %%
def stretch():
    # BEGIN SOLUTION
    rest = done[done.urgent == 0]
    cold = M.add_cost(rest.assign(cached_tokens=0), region=REGION, batch=True).cost_sar.sum()
    warm = M.add_cost(rest.assign(cached_tokens=1024), region=REGION, batch=True).cost_sar.sum()
    print(f"batch without cache {M.sar(cold)} | with 1,024 cached tokens per request {M.sar(warm)} | {1 - warm / cold:.1%} more off: "
          f"the stable part is {1024 / rest.input_tokens.mean():.0%} of an average prompt; the transcript is the rest and never repeats")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A batch is submitted every 4 hours and takes a median of 38 minutes. What is the median turnaround of a call?
#    <details><summary>Answer</summary>About 2 hours of waiting on average plus the completion time: near 2 hours
#    40 minutes. The schedule, not the provider, is most of the wait.</details>
# 2. Which workloads belong on a batch tier?
#    <details><summary>Answer</summary>Those where nobody waits for the single answer: summaries, evaluations,
#    backfills, nightly reports. Anything with a person waiting stays interactive.</details>
# 3. The provider's page says "50% off". What do you write in the review?
#    <details><summary>Answer</summary>The measured saving for this job with its urgent calls kept interactive,
#    and the share of summaries that arrive on time under the chosen schedule.</details>
#
# **Carry forward.** The plan table goes into the review of Lab 3.4.
