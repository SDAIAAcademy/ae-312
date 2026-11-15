# %% [markdown]
# # Lab 3.3 · Cost per resolved dispute
#
# Day 3 · Session 3 (Cost per successful outcome) · 25 min.
#
# Since 16 October half of the dispute agent's sessions run on a cheaper configuration: the medium tier in place of
# the large one. Per request it costs a quarter. Humoud Al-Rubaian, who owns the agent, does not buy requests: he
# needs disputes resolved, correctly. You join the cost of each session with its reviewed outcome, compute three
# unit costs, compare the two configurations at the quality floor, and add what the model's failures cost in
# people.
#
# **AI policy: tutor.** An assistant may explain a join. The denominators and the conclusion are yours.
#
# **Reference state.** `data/usage.csv.gz`, `data/outcomes/disputes.csv` (one reviewed outcome per session, where a
# review exists), `data/outcomes/human_cost.json`. All synthetic. No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · Join session cost with outcomes, and count what did not join (6')
# - [ ] 2 · Three unit costs: request, session, resolved dispute (6')
# - [ ] 3 · Two configurations at the quality floor (7')
# - [ ] 4 · Add the cost of human escalations (6')
# - [ ] ✱ Stretch · An interval for the difference, by resampling sessions

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

import duckdb
import numpy as np
import pandas as pd

import mawj as M

# %%
u = M.add_cost(M.attribute(M.usage()))
f = u[(u.app == "fasil") & (u.env == "prod")]
sessions = f.groupby("session_id").agg(cost_sar=("cost_sar", "sum"), requests=("status", lambda s: int((s == "ok").sum())),
                                       day=("ts", lambda t: t.iloc[0].day), model=("model", "first")).reset_index()
outcomes = pd.read_csv(M.DATA / "outcomes" / "disputes.csv")
HUMAN = M.load_json("outcomes/human_cost.json")
print(f"{len(sessions):,} sessions in the log, {M.sar(sessions.cost_sar.sum())} | {len(outcomes):,} reviewed outcomes")
print(outcomes.outcome.value_counts().to_string())
print(HUMAN)

# %% [markdown]
# ## 1 · Join, and count what did not join (6')
#
# Cost lives in the gateway log; outcomes live in the review tool of billing operations. A join between two
# systems never matches completely, and what falls out changes the answer.
#
# ✏️ **Exercise** · Write `join_outcomes(sessions, outcomes)` returning three things: the joined frame (sessions
# that have an outcome, with `config` and `outcome`), the number of sessions **without** an outcome, and the number
# of outcomes **without** a session.

# %%
def join_outcomes(sessions, outcomes):
    # BEGIN SOLUTION
    joined = sessions.merge(outcomes, on="session_id", how="inner")
    no_outcome = int((~sessions.session_id.isin(outcomes.session_id)).sum())
    no_session = int((~outcomes.session_id.isin(sessions.session_id)).sum())
    return joined, no_outcome, no_session
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    j, no_outcome, no_session = join_outcomes(sessions, outcomes)
except NotImplementedError:
    j = sessions.merge(outcomes, on="session_id", how="inner")
    no_outcome, no_session = M.reference("d3_3_join")["no_outcome"], M.reference("d3_3_join")["no_session"]
unreviewed_cost = float(sessions[~sessions.session_id.isin(outcomes.session_id)].cost_sar.sum())
M.keep("d3_3_join", {"joined": len(j), "no_outcome": no_outcome, "no_session": no_session, "unreviewed_cost_sar": round(unreviewed_cost, 2)})
print(f"joined {len(j):,} | sessions without an outcome {no_outcome} ({M.sar(unreviewed_cost)}) | outcomes without a session {no_session}")
M.check(len(j) + no_outcome == len(sessions) and no_session > 0, "every session is either joined or counted as unreviewed, and some outcomes belong to no production session")

# %% [markdown]
# 🔍 The unreviewed sessions were paid for. Leaving them out of the cost makes every unit cost look better;
# keeping their cost and not their outcome makes it look worse. Say which you did: below, unit costs use the
# joined sessions only, and the unreviewed spend is reported beside them.

# %% [markdown]
# ## 2 · Three unit costs (6')
#
# ✏️ **Exercise** · Write `unit_costs(j)`: a dictionary with `per_request` (cost over successful requests),
# `per_session` and `per_resolved` (cost of **all** joined sessions over the sessions whose outcome is
# `resolved_correct`).

# %%
def unit_costs(j):
    # BEGIN SOLUTION
    total = j.cost_sar.sum()
    return {"per_request": float(total / j.requests.sum()), "per_session": float(total / len(j)),
            "per_resolved": float(total / (j.outcome == "resolved_correct").sum())}
    # END SOLUTION


# %%
def _unit_costs(j):
    try:
        return unit_costs(j)
    except NotImplementedError:
        total = j.cost_sar.sum()
        return {"per_request": float(total / j.requests.sum()), "per_session": float(total / len(j)),
                "per_resolved": float(total / (j.outcome == "resolved_correct").sum())}


units = _unit_costs(j)
M.keep("d3_3_units", units)
print({k: round(v, 4) for k, v in units.items()})
M.check(units["per_request"] < units["per_session"] < units["per_resolved"], "each unit is dearer than the one before: the same money over fewer things")

# %% [markdown]
# ## 3 · Two configurations at the quality floor (7')
#
# Compare like with like: configuration B started on day 16, and day 17 was the incident. Use the sessions from day
# 16 on, without day 17. The floor for this agent in production, set by Humoud: of the disputes the agent resolves,
# at most 6% may be resolved wrongly.
#
# ✏️ **Exercise** · Write `by_config(c)`: one row per `config` with `sessions`, `resolved_correct`, `escalated`,
# `resolved_wrong` (shares of sessions), `wrong_share_of_resolved`, `per_session` and `per_resolved` (model cost).

# %%
c = j[(j.day >= 16) & (j.day != 17)]
FLOOR_WRONG = HUMAN["floor"]["max_wrong_share_of_resolved"]


def by_config(c):
    # BEGIN SOLUTION
    return duckdb.sql("""
        select config, count(*) as sessions,
               avg((outcome = 'resolved_correct')::int) as resolved_correct,
               avg((outcome = 'escalated')::int) as escalated,
               avg((outcome = 'resolved_wrong')::int) as resolved_wrong,
               sum((outcome = 'resolved_wrong')::int) / sum((outcome like 'resolved%')::int) as wrong_share_of_resolved,
               sum(cost_sar) / count(*) as per_session,
               sum(cost_sar) / sum((outcome = 'resolved_correct')::int) as per_resolved
        from c group by config order by config
    """).df()
    # END SOLUTION


# %%
try:
    cfg = by_config(c)
except NotImplementedError:
    cfg = M.reference("d3_3_by_config")
cfg["meets_floor"] = cfg.wrong_share_of_resolved <= FLOOR_WRONG
M.keep("d3_3_by_config", cfg)
print(cfg.round(4).to_string(index=False))
a, b = cfg.set_index("config").loc["A"], cfg.set_index("config").loc["B"]
print(f"\nB against A, model cost only: per session {b.per_session / a.per_session:.0%}, per resolved dispute {b.per_resolved / a.per_resolved:.0%}")
M.check(b.per_resolved < a.per_resolved and not b.meets_floor and a.meets_floor,
        "on the model's bill B is cheaper per resolved dispute, and B fails the floor on wrong resolutions")

# %% [markdown]
# 🔍 Offline, configuration B passed its floor by one task (Lab 2.1's stretch). In production it resolves fewer
# disputes, escalates twice as often and resolves more of them wrongly. An evaluation set is a sample taken on one
# day; outcomes are what happened.

# %% [markdown]
# ## 4 · Add the cost of human escalations (6')
#
# A dispute the agent escalates is handled by a person: SAR 21. A dispute it resolves wrongly comes back and is
# reworked: SAR 55. Those are costs of the configuration too.
#
# ✏️ **Exercise** · Write `full_cost_per_resolved(c)`: per `config`, the model cost plus the human cost of
# escalations and wrong resolutions, over the correctly resolved disputes. Return a Series indexed by `config`.

# %%
def full_cost_per_resolved(c):
    # BEGIN SOLUTION
    human = (c.outcome == "escalated") * HUMAN["escalation_to_a_human"] + (c.outcome == "resolved_wrong") * HUMAN["rework_of_a_wrong_resolution"]
    g = c.assign(total=c.cost_sar + human, good=(c.outcome == "resolved_correct")).groupby("config")
    return g.total.sum() / g.good.sum()
    # END SOLUTION


# %%
try:
    full = full_cost_per_resolved(c)
except NotImplementedError:
    full = pd.Series(M.reference("d3_3_full"))
M.keep("d3_3_full", full.to_dict())
result = pd.DataFrame({"model_only": cfg.set_index("config").per_resolved, "with_people": full})
result["model_share_pct"] = 100 * result.model_only / result.with_people
print(result.round(3).to_string())
M.keep("d3_3_summary", {"per_resolved_model_only": result.model_only.round(3).to_dict(), "per_resolved_with_people": result.with_people.round(3).to_dict(),
                        "units_all_sessions": {k: round(v, 4) for k, v in units.items()}, "b_meets_floor": bool(b.meets_floor)})
print(f"\ncost per resolved dispute, people included: A {M.sar(full['A'])}, B {M.sar(full['B'])}: B costs {full['B'] / full['A']:.1f} times A")
M.check(full["B"] > full["A"], "with the people who handle its failures, the cheaper configuration is the dearer one")

# %% [markdown]
# 🔍 The model's bill is the smaller part of what a resolved dispute costs. A cost review that stops at the
# invoice would have recommended B.

# %% [markdown]
# ## ✱ Stretch · An interval for the difference
#
# Resample the sessions of each configuration with replacement 500 times and compute B minus A in full cost per
# resolved dispute each time. Report the middle 95% of the differences. Does it include zero?

# %%
def stretch():
    # BEGIN SOLUTION
    rng = np.random.default_rng(312)
    human = (c.outcome == "escalated") * HUMAN["escalation_to_a_human"] + (c.outcome == "resolved_wrong") * HUMAN["rework_of_a_wrong_resolution"]
    x = c.assign(total=c.cost_sar + human, good=(c.outcome == "resolved_correct").astype(int))
    xa, xb = x[x.config == "A"][["total", "good"]].to_numpy(), x[x.config == "B"][["total", "good"]].to_numpy()
    diffs = []
    for _ in range(M.pick(500, 100)):
        sa, sb = xa[rng.integers(0, len(xa), len(xa))], xb[rng.integers(0, len(xb), len(xb))]
        diffs.append(sb[:, 0].sum() / sb[:, 1].sum() - sa[:, 0].sum() / sa[:, 1].sum())
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    print(f"B minus A, full cost per resolved dispute: SAR {np.mean(diffs):.2f}, middle 95% from {lo:.2f} to {hi:.2f}")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. Configuration B costs a quarter of A per request. Name two things that have to be true before that is a
#    saving.
#    <details><summary>Answer</summary>B must hold the quality floor, and the work B fails to do must not cost more
#    elsewhere (people, rework, lost customers) than B saves on the invoice.</details>
# 2. 4% of sessions have no reviewed outcome. Where do they go in "cost per resolved dispute"?
#    <details><summary>Answer</summary>Either leave both their cost and their outcome out and report their spend
#    beside the number, or include both once reviewed. Mixing (cost in, outcome out) biases the number.</details>
# 3. Why compare the two configurations from day 16 on and without day 17?
#    <details><summary>Answer</summary>B did not exist before day 16, and the incident day's loops are not a
#    property of either configuration. Same period, same conditions.</details>
#
# **Carry forward.** The two unit costs per configuration go into the review of Lab 3.4.
