# %% [markdown]
# # Lab 1.2 · The ten most expensive sessions
#
# Day 1 · Session 2 (Agents, retries and long contexts) · 25 min.
#
# A request has a price; a session has a bill. You find the ten most expensive sessions of October, split each bill
# into four parts (the base work, context growth, extra steps, retries), read the worst one step by step and size
# a fix for each cause over the whole month.
#
# **AI policy: tutor.** An assistant may explain a query or an error. The split and its reading are yours.
#
# **Reference state.** `data/usage.csv.gz` and the cost model of Lab 1.1 (`M.add_cost`). No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · Cost per session, and the top ten (5')
# - [ ] 2 · Split each session: base, context growth, extra steps, retries (9')
# - [ ] 3 · Read the worst session step by step (5')
# - [ ] 4 · Three causes, three fixes and their size (6')
# - [ ] ✱ Stretch · What the agent would cost without its prefix cache

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
import pandas as pd

import mawj as M

# %%
u = M.add_cost(M.with_register(M.usage()))
print(f"{len(u):,} rows | {u.session_id.nunique():,} sessions | {M.sar(u.cost_sar.sum())} on the hosted tiers")

# %% [markdown]
# ## 1 · Cost per session, and the top ten (5')
#
# ✏️ **Exercise** · Build `sessions`: one row per `session_id` with `app`, `cost_sar`, `rows` (attempts), `steps`
# (the highest step), `first_ts` and `max_input` (the largest prompt), most expensive first. DuckDB or pandas.

# %%
def session_table(u):
    # BEGIN SOLUTION
    return duckdb.sql("""
        select session_id, any_value(app) as app, sum(cost_sar) as cost_sar, count(*) as "rows",
               max(step) as steps, min(ts) as first_ts, max(input_tokens) as max_input
        from u group by session_id order by cost_sar desc, session_id
    """).df()
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    sessions = session_table(u)
except NotImplementedError:
    sessions = M.reference("d1_2_sessions_top")
top = sessions.head(10).copy()
M.keep("d1_2_sessions_top", sessions.head(200))
print(top.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
median_fasil = sessions[sessions.app == "fasil"].cost_sar.median()
print(f"\nmedian Fasil session: SAR {median_fasil:.3f} | the most expensive one costs {top.cost_sar.iloc[0] / median_fasil:.0f} times that")
M.check(top.cost_sar.is_monotonic_decreasing and set(top.app) == {"fasil"}, "the ten most expensive sessions are all sessions of the dispute agent")

# %% [markdown]
# 🔍 Two kinds of session are in this table. Look at `steps`, `max_input` and the day in `first_ts` and name them
# before you split anything.

# %% [markdown]
# ## 2 · Split each session into four parts (9')
#
# For the dispute agent, every billed row falls into one of four parts:
#
# | Part | Rows | Amount |
# |---|---|---|
# | `retries` | billed attempts that did not succeed (timeouts) | their whole cost |
# | `extra_steps` | successful steps beyond the step budget (12) | their whole cost |
# | `context_growth` | successful steps within the budget | the input cost of the tokens **beyond the first step's prompt** |
# | `base` | successful steps within the budget | the rest |
#
# The cell below adds `input_cost` (uncached plus cached input) and `first_input` (the prompt size of the session's
# first successful step) to the agent's rows.
#
# ✏️ **Exercise** · Write `split_rows(f, step_budget=12)` returning a frame with the four columns, one row per row
# of `f`. The four parts of a row add up to its `cost_sar`.

# %%
P = M.prices()["tiers"]
f = u[(u.app == "fasil") & (u.env == "prod")].sort_values(["session_id", "ts"]).copy()
f["input_cost"] = ((f.input_tokens - f.cached_tokens) * f.model.map(lambda m: P[m]["input"])
                   + f.cached_tokens * f.model.map(lambda m: P[m]["cached_input"])) / 1e6
f["input_cost"] = f.input_cost.where(f.status.isin(["ok", "timeout"]), 0.0)
f["first_input"] = f.session_id.map(f[f.status == "ok"].groupby("session_id").input_tokens.first())
f["first_input"] = f.first_input.fillna(f.input_tokens)


def split_rows(f, step_budget=12):
    # BEGIN SOLUTION
    ok = f.status == "ok"
    within = ok & (f.step <= step_budget)
    growth = (f.input_cost * (f.input_tokens - f.first_input).clip(lower=0) / f.input_tokens).where(within, 0.0)
    return pd.DataFrame({
        "base": f.cost_sar.where(within, 0.0) - growth,
        "context_growth": growth,
        "extra_steps": f.cost_sar.where(ok & (f.step > step_budget), 0.0),
        "retries": f.cost_sar.where(~ok, 0.0),
    })
    # END SOLUTION


# %%
PARTS = ["base", "context_growth", "extra_steps", "retries"]
try:
    parts = split_rows(f)
    by_session = pd.concat([f[["session_id"]], parts], axis=1).groupby("session_id")[PARTS].sum()
except NotImplementedError:
    by_session = M.reference("d1_2_split_all").set_index("session_id")
M.keep("d1_2_split_all", by_session.round(6).reset_index())
split_top = by_session.loc[top.session_id].copy()
split_top["cost_sar"] = split_top[PARTS].sum(axis=1)
split_top["main_cause"] = split_top[PARTS[1:]].idxmax(axis=1)
print(split_top.round(2).to_string())
M.check(abs(by_session[PARTS].sum().sum() - f.cost_sar.sum()) < 0.01, "the four parts add up to the agent's bill for the month")
M.check(set(split_top.main_cause) >= {"extra_steps", "context_growth"}, "the top ten hold both kinds: sessions that loop and sessions that carry a long context")

# %% [markdown]
# ## 3 · Read the worst session step by step (5')
#
# A table of parts says what; the steps say why.
#
# ✏️ **Exercise** · Write `half_cost_step(rows)`: the step at which the session has spent half of its cost.

# %%
worst = f[f.session_id == top.session_id.iloc[0]].copy()
worst["grew_by"] = worst.input_tokens.diff().fillna(0).astype(int)
worst["cumulative_sar"] = worst.cost_sar.cumsum()
print(worst[["ts", "step", "attempt", "status", "input_tokens", "grew_by", "cached_tokens", "reasoning_tokens", "cost_sar", "cumulative_sar"]]
      .iloc[list(range(8)) + list(range(len(worst) - 4, len(worst)))].to_string(index=False, float_format=lambda x: f"{x:.3f}"))


def half_cost_step(rows):
    # BEGIN SOLUTION
    cum = rows.cost_sar.cumsum()
    return int(rows.step[cum >= cum.iloc[-1] / 2].iloc[0])
    # END SOLUTION


# %%
try:
    half = half_cost_step(worst)
except NotImplementedError:
    half = M.reference("d1_2_half_step")
M.keep("d1_2_half_step", half)
print(f"session {worst.session_id.iloc[0]}: {int(worst.step.max())} steps, {len(worst)} attempts, {int((worst.status == 'timeout').sum())} billed timeouts; "
      f"half of its cost was spent by step {half}")
M.check(half > int(worst.step.max()) / 2, "the second half of the steps costs more than the first: every step resends a longer history")

# %% [markdown]
# 🔍 From step 3 on the prompt grows by a few hundred tokens per step: the billing system answered "pending" and
# the agent asked again, on 17 October, for an afternoon. Nobody had told it when to stop.

# %% [markdown]
# ## 4 · Three causes, three fixes and their size (6')
#
# | Cause | Part | Fix |
# |---|---|---|
# | The agent loops | `extra_steps` | a step budget, and a stop rule for "pending" |
# | The provider times out and the client retries at once | `retries` | fewer attempts, a pause between them, a circuit breaker |
# | A tool returns a year of bills on every call | `context_growth` | page and trim tool results |
#
# ✏️ **Exercise** · Compute `month`: the four parts summed over all sessions of the agent, in SAR and as a share
# of its bill. Then `long_context`: the `context_growth` of the sessions in which one step's prompt grew by more than
# 20,000 tokens.

# %%
biggest_jump = f.assign(jump=f.groupby("session_id").input_tokens.diff()).groupby("session_id").jump.max()



def month_parts(by_session, biggest_jump):
    """Return (month, long_context)."""
    # BEGIN SOLUTION
    month = pd.DataFrame({"sar": by_session[PARTS].sum()})
    month["share_pct"] = 100 * month.sar / month.sar.sum()
    long_context = float(by_session.loc[biggest_jump[biggest_jump > 20000].index, "context_growth"].sum())
    return month, long_context
    # END SOLUTION


# %%
try:
    month, long_context = month_parts(by_session, biggest_jump)
except NotImplementedError:
    month, long_context = M.reference("d1_2_month").set_index("part"), M.reference("d1_2_long_context")
M.keep("d1_2_month", month.rename_axis("part").reset_index())
M.keep("d1_2_long_context", long_context)
print(month.round(2).to_string())
print(f"\nsessions with a jump above 20,000 tokens: {int((biggest_jump > 20000).sum())} of {len(biggest_jump)}; their context growth costs {M.sar(long_context)}")
print(f"sizes of the three fixes: step budget {M.sar(month.sar['extra_steps'])} | retry policy {M.sar(month.sar['retries'])} | paged tool results up to {M.sar(long_context)}")
M.check(month.sar["extra_steps"] > month.sar["retries"], "on this month the loop cost more than the retries")

# %% [markdown]
# 🔍 The `retries` part is small in SAR. Before you drop it from the list: every billed timeout was also a customer
# who waited a minute for nothing. Cost is one of the reasons to fix it, not the only one.

# %% [markdown]
# ## ✱ Stretch · Without the prefix cache
#
# The agent resends its whole history at every step, and the provider bills most of it at the cached price.
# Recompute the agent's month as if no token had been cached. What does that say about changing the model in the
# middle of a session (Lab 2.2)?

# %%
def stretch():
    # BEGIN SOLUTION
    no_cache = M.add_cost(f.assign(cached_tokens=0)).cost_sar.sum()
    print(f"with the cache {M.sar(f.cost_sar.sum())} | without it {M.sar(no_cache)} | the cache is worth {100 * (1 - f.cost_sar.sum() / no_cache):.0f}% of the agent's bill")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. An agent takes twice as many steps as planned. Does the session cost twice as much?
#    <details><summary>Answer</summary>More: every step resends the history so far, so input grows with the square
#    of the steps unless the history is cached, trimmed or summarised.</details>
# 2. Why is "average cost per request" a poor number for an agent?
#    <details><summary>Answer</summary>The unit of work is the session. A few sessions hold a large share of the
#    bill, and the average request hides them.</details>
# 3. Which of the three fixes would you ship first, and what would you measure after it?
#    <details><summary>Answer</summary>The step budget: the largest part, the smallest change, and a failure that is
#    easy to see. Measure the share of sessions that hit the budget and what happened to their disputes.</details>
#
# **Carry forward.** Lab 1.4 replays 17 October through the gateway. Nothing is saved here.
