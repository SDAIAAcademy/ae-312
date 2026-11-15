# %% [markdown]
# # Lab 1.4 · Soft and hard budgets, and a spike
#
# Day 1 · Session 4 (Budgets and limits) · 25 min.
#
# On 17 October a tool outage made the dispute agent loop for an afternoon. Maabar had one budget for the whole
# gateway. You replay that day, see who was refused, write budgets per application with a soft and a hard level,
# trip the hard limit on the agent without touching the care assistant, and add a rate limit.
#
# **AI policy: tutor.** An assistant may explain the policy format. The levels are your decision.
#
# **Reference state.** `data/gateway/replay_calm_day.csv.gz` (14 October), `data/gateway/replay_incident_day.csv.gz`
# (17 October), `data/gateway/policy_start.json`, and `maabar.py`, a small model of a gateway that replays log rows
# and keeps budgets in memory. No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · Read the policy and replay a calm day (5')
# - [ ] 2 · Replay the spike under one global budget (5')
# - [ ] 3 · Budgets per application: soft and hard (8')
# - [ ] 4 · Trip the hard limit and read the gateway log (4')
# - [ ] 5 · A requests-per-minute limit for the agent (3')
# - [ ] ✱ Stretch · A budget per environment, so that staging cannot spend production money

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

import maabar
import mawj as M

# %%
calm = M.read_usage(M.DATA / "gateway" / "replay_calm_day.csv.gz")
spike = M.read_usage(M.DATA / "gateway" / "replay_incident_day.csv.gz")
START = M.load_json("gateway/policy_start.json")
print(json.dumps(START, indent=1))
print(f"calm day: {len(calm):,} rows | incident day: {len(spike):,} rows")

# %% [markdown]
# ## 1 · Read the policy and replay a calm day (5')
#
# `maabar.Gateway(policy).replay(rows)` returns the rows with the gateway's `decision` (`allowed` or `refused`), a
# `reason`, the `cost_sar` the request would have and `spent_sar`, which is 0 for a refused request. A soft level
# writes an alert to `event_log()`; a hard level refuses every later request in its scope until the window (a day)
# ends.
#
# ✏️ **Exercise** · Write `summarise(log)`: one row per `app` with `requests`, `refused` and `spent_sar`.

# %%
def summarise(log):
    # BEGIN SOLUTION
    return log.groupby("app").agg(requests=("decision", "size"), refused=("decision", lambda d: int((d == "refused").sum())),
                                  spent_sar=("spent_sar", "sum")).reset_index()
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
def _summarise(log):
    try:
        return summarise(log)
    except NotImplementedError:
        return log.groupby("app").agg(requests=("decision", "size"), refused=("decision", lambda d: int((d == "refused").sum())),
                                      spent_sar=("spent_sar", "sum")).reset_index()


gw = maabar.Gateway(START)
calm_log = gw.replay(calm)
calm_summary = _summarise(calm_log)
print(calm_summary.round(2).to_string(index=False))
print(gw.event_log().to_string(index=False) if len(gw.events) else "no alert, no refusal")
M.check(calm_summary.refused.sum() == 0, "on a calm day the global budget refuses nothing")

# %% [markdown]
# ## 2 · Replay the spike under one global budget (5')
#
# ✏️ **Exercise** · The cell replays the incident day under `START`. Write `read_refusals(log)` returning
# `first_refusal` (the time of the first refused request) and `refused_by_app` (a Series: refused requests per
# application).

# %%
gw = maabar.Gateway(START)
spike_log = gw.replay(spike)



def read_refusals(log):
    # BEGIN SOLUTION
    refused = log[log.decision == "refused"]
    return refused.ts.min(), refused.groupby("app").size()
    # END SOLUTION


# %%
try:
    first_refusal, refused_by_app = read_refusals(spike_log)
except NotImplementedError:
    r = M.reference("d1_4_global")
    first_refusal, refused_by_app = pd.Timestamp(r["first_refusal"]), pd.Series(r["refused_by_app"])
M.keep("d1_4_global", {"first_refusal": str(first_refusal), "refused_by_app": refused_by_app.to_dict(),
                       "refused_customers": int(spike_log[(spike_log.decision == "refused") & (spike_log.app == "anis")].customer_id.nunique())})
print(gw.event_log().to_string(index=False))
print(f"\nfirst refusal at {first_refusal:%H:%M} on the incident day; refused requests by application:")
print(refused_by_app.to_string())
print(f"customers of the care assistant who got no answer that evening: {spike_log[(spike_log.decision == 'refused') & (spike_log.app == 'anis')].customer_id.nunique():,}")
M.check(refused_by_app.get("anis", 0) > refused_by_app.get("fasil", 0), "the global budget refused more requests of the care assistant than of the agent that caused the spike")

# %% [markdown]
# 🔍 The agent spent the gateway's budget in the afternoon; the care assistant paid for it in the evening, its
# busiest hours. The budget worked and protected the wrong thing: its **scope** was the problem, not its level.

# %% [markdown]
# ## 3 · Budgets per application: soft and hard (8')
#
# Levels come from data, not from a round number. The table below is each application's daily spend over the month
# without the incident day. A common rule: the hard level at about one and a half times the highest normal day, the
# soft level at 80% of the hard one.
#
# ✏️ **Exercise** · Write `app_policy()` returning the policy: one budget per application for `anis`, `khulasa` and `fasil`
# (`{"scope": "app", "match": ..., "soft_sar": ..., "hard_sar": ...}`), window `day`, no rate limit yet.

# %%
month = M.add_cost(M.attribute(M.usage()))
daily = month[month.ts.dt.day != 17].groupby(["app", month.ts.dt.day]).cost_sar.sum().groupby("app").agg(["median", "max"]).round(1)
print(daily.loc[["anis", "khulasa", "fasil"]].to_string())



def app_policy():
    # BEGIN SOLUTION
    return {"window": "day", "budgets": [
        {"scope": "app", "match": "anis", "soft_sar": 48.0, "hard_sar": 60.0},
        {"scope": "app", "match": "khulasa", "soft_sar": 56.0, "hard_sar": 70.0},
        {"scope": "app", "match": "fasil", "soft_sar": 132.0, "hard_sar": 165.0},
    ], "rate_limits": []}
    # END SOLUTION


# %%
try:
    POLICY = app_policy()
except NotImplementedError:
    POLICY = M.reference("d1_4_policy")
M.keep("d1_4_policy", POLICY)
gw_calm = maabar.Gateway(POLICY)
calm2 = _summarise(gw_calm.replay(calm))
M.check(calm2.refused.sum() == 0 and len(gw_calm.events) == 0, "the new policy is silent on a calm day: no alert, no refusal")
M.check({b["match"] for b in POLICY["budgets"]} >= {"anis", "khulasa", "fasil"} and all(b["scope"] == "app" for b in POLICY["budgets"]),
        "one budget per application")

# %% [markdown]
# ## 4 · Trip the hard limit and read the gateway log (4')
#
# ✏️ **Exercise** · The cell replays the incident day under `POLICY`. Write `cost_not_spent(log)`: the cost the
# refused requests would have had.

# %%
gw = maabar.Gateway(POLICY)
log = gw.replay(spike)
events = gw.event_log()



def cost_not_spent(log):
    # BEGIN SOLUTION
    return float(log[log.decision == "refused"].cost_sar.sum())
    # END SOLUTION


# %%
try:
    not_spent = cost_not_spent(log)
except NotImplementedError:
    not_spent = M.reference("d1_4_result")["not_spent_sar"]
summary = _summarise(log)
print(events.to_string(index=False))
print(summary.round(2).to_string(index=False))
out = M.lab_dir("D1_4")
log[["request_id", "ts", "key_id", "app", "env", "team", "session_id", "decision", "reason", "cost_sar", "spent_sar"]].to_csv(out / "gateway_log.csv", index=False)
refused_sessions = log[log.decision == "refused"].session_id.nunique()
print(f"\nrefused: {int((log.decision == 'refused').sum())} requests in {refused_sessions} sessions | not spent: {M.sar(not_spent)} | log written to artifacts/D1_4/gateway_log.csv")
M.keep("d1_4_result", {"not_spent_sar": round(not_spent, 2), "fasil_spent_sar": round(float(summary.set_index("app").spent_sar["fasil"]), 2),
                       "refused_requests": int((log.decision == "refused").sum()), "refused_sessions": int(refused_sessions),
                       "events": [{**e, "ts": str(e["ts"])} for e in gw.events]})
by_app = summary.set_index("app")
M.check(by_app.refused["fasil"] > 0 and by_app.refused["anis"] == 0, "the hard limit tripped on the agent, and the care assistant answered every customer")
M.check(list(events.event) == ["soft_alert", "hard_limit_reached"], "the soft alert came before the hard limit")

# %% [markdown]
# 🔍 Between the soft alert and the hard limit there was time for a person to look. What should the alert say,
# and to whom, so that it is used? A replay refuses rows one by one; in production a refused step ends the agent's
# session, so the real saving is larger and the customers of those sessions need a human.

# %% [markdown]
# ## 5 · A requests-per-minute limit for the agent (3')
#
# A budget counts money over a day. A rate limit counts requests (or tokens) over a minute: it slows a burst long
# before a daily budget notices. The busiest minute of the agent on the calm day is printed below.
#
# ✏️ **Exercise** · Write `with_rate_limit(policy, busiest)`: a copy of the policy with one rate limit for `fasil`
# (`{"scope": "app", "match": "fasil", "requests_per_minute": ...}`) at about twice the calm day's busiest minute.

# %%
calm_fasil = M.attribute(calm)
calm_fasil = calm_fasil[calm_fasil.app == "fasil"]
busiest = int(calm_fasil.set_index("ts").request_id.resample("1min").count().max())
print(f"calm day, the agent's busiest minute: {busiest} requests")



def with_rate_limit(policy, busiest):
    # BEGIN SOLUTION
    return {**policy, "rate_limits": [{"scope": "app", "match": "fasil", "requests_per_minute": 2 * busiest}]}
    # END SOLUTION


# %%
try:
    POLICY_RL = with_rate_limit(POLICY, busiest)
except NotImplementedError:
    POLICY_RL = {**POLICY, "rate_limits": [{"scope": "app", "match": "fasil", "requests_per_minute": 2 * busiest}]}
gw = maabar.Gateway(POLICY_RL)
log_rl = gw.replay(spike)
reasons = log_rl[log_rl.decision == "refused"].reason.str.split(":").str[0].value_counts()
first_rl = log_rl[log_rl.reason.str.startswith("rate_limited")].ts.min()
print(reasons.to_string())
print(f"first rate-limited request at {first_rl:%H:%M}; the hard budget was reached at {gw.event_log().query('event == \"hard_limit_reached\"').ts.min():%H:%M}")
M.keep("d1_4_rate_limit", {"requests_per_minute": POLICY_RL["rate_limits"][0]["requests_per_minute"], "refused": reasons.to_dict(), "first_rate_limited": str(first_rl)})
M.check(reasons.get("rate_limited", 0) > 0 and maabar.Gateway(POLICY_RL).replay(calm).decision.eq("allowed").all(),
        "the rate limit acts on the incident day and is silent on the calm day")

# %% [markdown]
# ## ✱ Stretch · A budget per environment
#
# Staging and development share the production keys' provider account. Add a budget with `"scope": "env"` for
# `staging` and one for `dev`, from the month's data, and check both replays.

# %%
def stretch():
    # BEGIN SOLUTION
    env_daily = month.groupby(["env", month.ts.dt.day]).cost_sar.sum().groupby("env").max().round(1)
    print(env_daily.to_string())
    POLICY_ENV = {**POLICY_RL, "budgets": POLICY["budgets"] + [
        {"scope": "env", "match": "staging", "soft_sar": 12.0, "hard_sar": 15.0},
        {"scope": "env", "match": "dev", "soft_sar": 12.0, "hard_sar": 15.0}]}
    for name, rows in (("calm", calm), ("incident", spike)):
        r = maabar.Gateway(POLICY_ENV).replay(rows)
        print(name, r[r.decision == "refused"].groupby("env").size().to_dict())
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A soft budget and a hard budget are both reached. What does each one do?
#    <details><summary>Answer</summary>The soft one tells someone; the hard one refuses requests in its scope until
#    the window ends. Soft without hard is a message nobody has to act on; hard without soft is an outage without
#    warning.</details>
# 2. Why did the global budget hurt the care assistant?
#    <details><summary>Answer</summary>Its scope was the whole gateway, so the first application to overspend used
#    up everyone's allowance. A budget protects what is inside its scope from what is inside its scope.</details>
# 3. When is a rate limit the better tool?
#    <details><summary>Answer</summary>For bursts and loops: it acts within a minute and lets normal traffic
#    through. A budget is for the total over a day or a month.</details>
#
# **Carry forward.** `artifacts/D1_4/gateway_log.csv` is the kind of gateway log the capstone repository holds.
