# %% [markdown]
# # Lab 1.3 · A showback table from gateway keys
#
# Day 1 · Session 3 (Attribution and showback) · 25 min.
#
# Shurooq Al-Hamli, the finance business partner, has one invoice and five teams. You turn the gateway log into a
# showback table: who spent what, by team, application and environment, adding up to the invoice, with an honest
# row for what nobody owns. Showback shows each team its spend; nobody is charged yet.
#
# **AI policy: tutor.** An assistant may explain a join or a regular expression. The allocation choices are yours.
#
# **Reference state.** `data/usage.csv.gz`, `data/gateway/keys.csv` (the key register), `data/gateway/teams.csv`,
# `data/invoice.csv`. No earlier lab is needed.
#
# **Tasks**
# - [ ] 1 · Join the usage log to the key register (5')
# - [ ] 2 · Split the shared key by its tags (6')
# - [ ] 3 · Showback by team, application and environment (7')
# - [ ] 4 · Calls between applications: caller pays or owner pays (7')
# - [ ] ✱ Stretch · Spread the idle accelerator-hours by tokens and by requests

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
u = M.add_cost(M.usage())
keys = M.keys()
inv = M.invoice()
print(keys.to_string(index=False))
print(f"\n{len(u):,} rows on {u.key_id.nunique()} keys | {M.sar(u.cost_sar.sum())} | tags present on {100 * (u.tags != '').mean():.0f}% of rows")

# %% [markdown]
# ## 1 · Join the usage log to the key register (5')
#
# A gateway key is issued to one team, for one application, in one environment. That is the first attribution, and
# it costs nothing.
#
# ✏️ **Exercise** · Write `by_register(u, keys)`: join on `key_id` and return spend by `team`, `app` and `env`
# (columns `team`, `app`, `env`, `requests`, `cost_sar`), largest first.

# %%
def by_register(u, keys):
    # BEGIN SOLUTION
    return duckdb.sql("""
        select k.team, k.app, k.env, count(*) as requests, sum(u.cost_sar) as cost_sar
        from u join keys k using (key_id)
        group by all order by cost_sar desc
    """).df()
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    reg = by_register(u, keys)
except NotImplementedError:
    reg = M.reference("d1_3_by_register")
M.keep("d1_3_by_register", reg)
print(reg.round(2).to_string(index=False))
M.check(abs(reg.cost_sar.sum() - u.cost_sar.sum()) < 0.01 and reg.requests.sum() == len(u), "every row has a key in the register, and the table adds up")

# %% [markdown]
# 🔍 The register says that contact-centre analytics spent more than customer care. Look at the note on
# `key-shared-legacy` before you send that table to anyone.

# %% [markdown]
# ## 2 · Split the shared key by its tags (6')
#
# `key-shared-legacy` was issued before Maabar had keys per application. Requests on it carry tags such as
# `app=khulasa`, `app=netlab-exp;team=network-analytics` or `app=khulasa;caller=fasil`, and some carry none.
# `M.tag(u, "app")` reads one tag.
#
# ✏️ **Exercise** · Write `attribute(u, keys)` returning `u` with `team`, `app` and `env`:
# a tag `app` or `team` wins over the register; a row on the shared key with **no** `app` tag is
# `unallocated` in both `team` and `app` (you do not know whose it is, so you do not guess).

# %%
def attribute(u, keys):
    # BEGIN SOLUTION
    out = u.merge(keys[["key_id", "team", "app", "env"]], on="key_id", how="left")
    tag_app, tag_team = M.tag(out, "app"), M.tag(out, "team")
    out["app"] = tag_app.where(tag_app != "", out["app"])
    out["team"] = tag_team.where(tag_team != "", out["team"])
    unknown = (out.key_id == "key-shared-legacy") & (tag_app == "")
    out.loc[unknown, ["team", "app"]] = "unallocated"
    return out
    # END SOLUTION


# %%
try:
    a = attribute(u, keys)
except NotImplementedError:
    a = M.attribute(u)
shared = a[a.key_id == "key-shared-legacy"].groupby(["team", "app"]).agg(requests=("cost_sar", "size"), cost_sar=("cost_sar", "sum"))
M.keep("d1_3_shared_key", shared.reset_index())
print(shared.round(2).to_string())
M.check(set(shared.index.get_level_values("app")) == {"khulasa", "netlab-exp", "unallocated"}, "the shared key holds Khulasa, another team's experiment and untagged requests")

# %% [markdown]
# 🔍 A team that was never issued a key ran a week of experiments on the large tier, under Khulasa's name. Compare
# its cost per request with Khulasa's.

# %% [markdown]
# ## 3 · Showback by team, application and environment (7')
#
# The table finance needs adds up to the invoice. Two invoice items are not in the log at all: the node lease
# (the pilot of contact-centre analytics) and the provider key that bypasses the gateway.
#
# ✏️ **Exercise** · Write `build_showback(a, node_lease, direct_key)`: spend from `a` by `team`, `app`, `env`, then two more rows from the invoice:
# the node lease (team `contact-centre-analytics`, app `khulasa`, env `staging`, item `node lease`) and the direct
# key (`unallocated`, `unallocated`, `unknown`, item `provider key outside the gateway`). Columns: `team`, `app`,
# `env`, `item`, `cost_sar`.

# %%
node_lease = float(inv[inv.provider_key == "node-lease"].amount_sar.sum())
direct_key = float(inv[inv.provider_key == "up-direct-7q2f"].amount_sar.sum())



def build_showback(a, node_lease, direct_key):
    # BEGIN SOLUTION
    showback = a.groupby(["team", "app", "env"], as_index=False).cost_sar.sum().assign(item="tokens through the gateway")
    showback = pd.concat([showback, pd.DataFrame([
        {"team": "contact-centre-analytics", "app": "khulasa", "env": "staging", "item": "node lease", "cost_sar": node_lease},
        {"team": "unallocated", "app": "unallocated", "env": "unknown", "item": "provider key outside the gateway", "cost_sar": direct_key},
    ])], ignore_index=True)
    return showback[["team", "app", "env", "item", "cost_sar"]].sort_values("cost_sar", ascending=False)
    # END SOLUTION


# %%
try:
    showback = build_showback(a, node_lease, direct_key)
except NotImplementedError:
    showback = M.reference("d1_3_showback")
M.keep("d1_3_showback", showback)
print(showback.round(2).to_string(index=False))
by_team = showback.groupby("team").cost_sar.sum().sort_values(ascending=False)
print("\nBy team:")
print((pd.DataFrame({"sar": by_team, "share_pct": 100 * by_team / by_team.sum()})).round(1).to_string())
unallocated_pct = 100 * by_team.get("unallocated", 0.0) / by_team.sum()
M.keep("d1_3_summary", {"by_team_sar": by_team.round(2).to_dict(), "unallocated_pct": round(unallocated_pct, 2)})
M.check(abs(showback.cost_sar.sum() - inv.amount_sar.sum()) < 0.05, "the showback table adds up to the invoice")
M.check(0 < unallocated_pct < 5, f"unallocated spend is visible and small: {unallocated_pct:.1f}% of the invoice")

# %% [markdown]
# 🔍 Showback before chargeback: publish this table for a month or two before anyone is billed. The first
# reactions ("that is not ours", "why is staging so high?") fix the tags, and a team that is charged from a table
# it has never seen stops trusting the table.

# %% [markdown]
# ## 4 · Calls between applications: caller pays or owner pays (7')
#
# The dispute agent sometimes asks Khulasa for a summary of a customer's earlier calls. Those requests run under
# Khulasa's key and carry `caller=fasil`. Who pays? There is no settled method for agents that call agents: state
# the rule you chose and show what the other one would give.
#
# ✏️ **Exercise** · Write `team_totals(a, rule)` for `rule` in `"owner"` and `"caller"`: spend by team, where under
# `"caller"` the rows tagged `caller=fasil` move to `billing-operations`.

# %%
def team_totals(a, rule):
    # BEGIN SOLUTION
    team = a.team.where(~((rule == "caller") & (M.tag(a, "caller") == "fasil")), "billing-operations")
    return a.groupby(team).cost_sar.sum()
    # END SOLUTION


# %%
try:
    both = pd.DataFrame({"owner_pays": team_totals(a, "owner"), "caller_pays": team_totals(a, "caller")}).fillna(0.0)
except NotImplementedError:
    both = M.reference("d1_3_two_rules").set_index("team")
both["difference"] = both.caller_pays - both.owner_pays
M.keep("d1_3_two_rules", both.rename_axis("team").reset_index())
print(both.round(2).to_string())
moved = float(both.difference.clip(lower=0).sum())
print(f"\n{M.sar(moved)} moves between two teams with the rule; the gateway's total does not change")
M.check(abs(both.owner_pays.sum() - both.caller_pays.sum()) < 0.01 and moved > 0, "the rule moves money between teams, never the total")

# %% [markdown]
# ## ✱ Stretch · The idle accelerator-hours
#
# The node was busy for under a fifth of its leased hours. Charge the pilot's team only for busy hours and put the
# idle hours on the platform team, then spread those idle hours over all teams, once by their tokens and once by
# their requests. Which team gains most from which rule?

# %%
def stretch():
    # BEGIN SOLUTION
    g = M.gpu_hours()
    busy_share = g.busy_minutes.sum() / (g.leased.sum() * 60)
    idle = node_lease * (1 - busy_share)
    tokens = a.assign(tokens=a.input_tokens + a.output_tokens).groupby("team").tokens.sum()
    requests = a.groupby("team").size()
    spread = pd.DataFrame({"idle_by_tokens": idle * tokens / tokens.sum(), "idle_by_requests": idle * requests / requests.sum()})
    print(f"busy {100 * busy_share:.0f}% of leased hours | idle cost {M.sar(idle)}")
    print(spread.round(2).to_string())
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. 8% of the requests on a shared key have no tag. Finance suggests giving them to the key's owner. What do you
#    answer?
#    <details><summary>Answer</summary>Keep them in an "unallocated" row. Giving them to the owner hides the gap,
#    and the row is what makes someone fix the tags. The durable fix is a key per application.</details>
# 2. Why showback before chargeback?
#    <details><summary>Answer</summary>The first tables are wrong in ways only the teams can see. A month of
#    showback fixes tags and ownership before money moves.</details>
# 3. Under "caller pays", who has a reason to make Khulasa cheaper?
#    <details><summary>Answer</summary>Nobody directly: the owner no longer pays for those calls and the caller
#    cannot change the service. Any rule sets incentives; say which ones.</details>
#
# **Carry forward.** `M.attribute(df)` is this lab's attribution; the gateway of Lab 1.4 uses it.
