# %% [markdown]
# # Lab 3.1 · Break-even utilisation for self-hosting
#
# Day 3 · Session 1 (Self-hosting economics) · 25 min.
#
# Qutaiba's pilot served call summaries from a leased accelerator node at 23 times the API price (Lab 1.1). Was
# that the node, or how it was used? You fill a cost model for serving an open-weight model: capacity at a latency
# objective, cost per request against utilisation, break-even against API prices. Before any price, the operator's
# classification register says where each dataset may be processed.
#
# **AI policy: tutor.** An assistant may explain plotting syntax. The model and the recommendation are yours.
#
# **Reference state.** `data/hosting/throughput_benchmark.csv` (one node, the open-weight model, summary-shaped
# requests), `data/hosting/price_sheets.json`, `data/hosting/classification_register.csv`, the price sheet and the
# usage log. All synthetic. No earlier lab is needed and no model is called.
#
# **Tasks**
# - [ ] 1 · Capacity at the latency objective, from the benchmark (5')
# - [ ] 2 · Cost per request against utilisation (6')
# - [ ] 3 · Break-even against the API prices, as a chart (7')
# - [ ] 4 · The classification register first, then the recommendation (7')
# - [ ] ✱ Stretch · Lease the node one hour a night: does the nightly job change the answer?

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

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import mawj as M

# %%
bench = pd.read_csv(M.DATA / "hosting" / "throughput_benchmark.csv")
SHEET = M.load_json("hosting/price_sheets.json")
register = pd.read_csv(M.DATA / "hosting" / "classification_register.csv")
HOURS = SHEET["node"]["hours_per_month"]
print(bench.to_string(index=False))
print({k: v for k, v in SHEET["node"].items() if k != "description"}, SHEET["operations"]["share_of_an_engineer_per_month"])

u = M.attribute(M.usage())
kh = u[(u.app == "khulasa") & (u.env == "prod") & (u.status == "ok")]
N_MONTH = len(kh)
API = {  # SAR per summary on the hosted tiers, by region, from the month's real requests
    (tier, region): float(M.add_cost(kh.assign(model=tier), region=region).cost_sar.mean())
    for tier in ("tier-s", "tier-m") for region in ("global", "in-kingdom")}
print(f"\nKhulasa: {N_MONTH:,} summaries in October |", {f"{t} {r}": round(v, 4) for (t, r), v in API.items()})

# %% [markdown]
# ## 1 · Capacity at the latency objective (5')
#
# A node can always take more requests at once; each one then waits longer. Capacity is the throughput at the
# highest concurrency that still meets the objective.
#
# ✏️ **Exercise** · Write `capacity_per_hour(bench, p95_limit_s)`: requests per hour at the highest concurrency
# whose `p95_latency_s` is within the limit. With `None` as limit (a batch job) take the highest throughput.

# %%
def capacity_per_hour(bench, p95_limit_s):
    # BEGIN SOLUTION
    ok = bench if p95_limit_s is None else bench[bench.p95_latency_s <= p95_limit_s]
    return float(ok.requests_per_min.max() * 60)
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    CAP = capacity_per_hour(bench, SHEET["latency_objective"]["interactive_p95_seconds"])
    CAP_BATCH = capacity_per_hour(bench, None)
except NotImplementedError:
    CAP, CAP_BATCH = M.reference("d3_1_capacity")
M.keep("d3_1_capacity", [CAP, CAP_BATCH])
demand_share = N_MONTH / (CAP * HOURS)
print(f"capacity at p95 within 20 s: {CAP:,.0f} summaries an hour | without an objective: {CAP_BATCH:,.0f} | "
      f"Khulasa's whole month is {demand_share:.1%} of one node running all month")
M.check(CAP == 3600 and CAP_BATCH == 5760, "capacity read from the benchmark at the objective, and without one")

# %% [markdown]
# ## 2 · Cost per request against utilisation (6')
#
# A node costs the same every hour, used or idle. Utilisation is the share of its capacity that serves requests.
#
# ✏️ **Exercise** · Write `self_host_cost(utilisation, hourly_cost, capacity)`: SAR per request.

# %%
def self_host_cost(utilisation, hourly_cost, capacity):
    # BEGIN SOLUTION
    return hourly_cost / (capacity * utilisation)
    # END SOLUTION


# %%
NODE_ON_DEMAND = SHEET["node"]["on_demand_per_hour"]
NODE_RESERVED = SHEET["node"]["reserved_per_month"] / HOURS
OPS = SHEET["operations"]["share_of_an_engineer_per_month"] / HOURS
try:
    self_host_cost(0.5, 1.0, 1.0)
    cost_fn = self_host_cost
except NotImplementedError:
    cost_fn = lambda utilisation, hourly_cost, capacity: hourly_cost / (capacity * utilisation)   # noqa: E731
levels = pd.DataFrame({"utilisation": [0.01, 0.05, 0.18, 0.50, 0.90]})
levels["node_only_on_demand"] = cost_fn(levels.utilisation, NODE_ON_DEMAND, CAP)
levels["reserved_with_operations"] = cost_fn(levels.utilisation, NODE_RESERVED + OPS, CAP)
M.keep("d3_1_levels", levels)
print(levels.round(4).to_string(index=False))
print(f"hourly cost: on demand SAR {NODE_ON_DEMAND:.2f} | reserved SAR {NODE_RESERVED:.2f} | operations SAR {OPS:.2f}")
M.check(abs(cost_fn(0.5, 14.0, 3600) - 14.0 / 1800) < 1e-12, "cost per request is the hourly cost over the requests served in that hour")

# %% [markdown]
# 🔍 The pilot ran at 18% of its leased hours **and** far below the node's capacity within those hours. The October
# figure of SAR 0.77 a summary was a utilisation of about half a percent.

# %% [markdown]
# ## 3 · Break-even against the API prices (7')
#
# Break-even utilisation is where a request on the node costs what it costs on the API. Below it, the API is
# cheaper.
#
# ✏️ **Exercise** · Write `break_even(hourly_cost, capacity, api_price)`: the utilisation at which the two are
# equal.

# %%
def break_even(hourly_cost, capacity, api_price):
    # BEGIN SOLUTION
    return hourly_cost / (capacity * api_price)
    # END SOLUTION


# %%
HOURLY = NODE_RESERVED + OPS
try:
    be = {f"{tier}, {region}": break_even(HOURLY, CAP, API[(tier, region)]) for tier in ("tier-m", "tier-s") for region in ("global", "in-kingdom")}
except NotImplementedError:
    be = M.reference("d3_1_break_even")
M.keep("d3_1_break_even", be)
table = pd.DataFrame({"break_even_utilisation": be})
table["summaries_a_month_needed"] = (table.break_even_utilisation * CAP * HOURS).round(0)
table["times_todays_volume"] = (table.summaries_a_month_needed / N_MONTH).round(1)
print(table.round(3).to_string())

x = np.linspace(0.02, 1.0, 200)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(100 * x, HOURLY / (CAP * x), color="#0f6e6e", label="self-hosted: reserved node and operations")
for (tier, region), style in ((("tier-m", "in-kingdom"), "--"), (("tier-s", "in-kingdom"), ":")):
    ax.axhline(API[(tier, region)], color="#b5533c", linestyle=style, label=f"API {tier}, {region}")
ax.axvline(100 * demand_share, color="grey", linewidth=1, label="Khulasa today")
ax.set_ylim(0, 0.08)
ax.set_xlabel("utilisation of the node, %")
ax.set_ylabel("SAR per summary")
ax.set_title("Break-even utilisation: self-hosting against API prices (synthetic price sheets)")
ax.legend()
fig.tight_layout()
fig.savefig(M.lab_dir("D3_1") / "break_even.png", dpi=120)
plt.close(fig)
print("chart written to artifacts/D3_1/break_even.png")
M.check(be["tier-s, in-kingdom"] > be["tier-m, in-kingdom"] > demand_share, "break-even is far above today's utilisation, and further still against the small tier")

# %% [markdown]
# 🔍 Break-even moves when the API price moves. Lab 2.1 found that Khulasa keeps its floor on the small tier: the
# cheaper the tier that does the job, the more traffic a node needs before it pays.

# %% [markdown]
# ## 4 · The classification register first (7')
#
# Price comes second. Yaqoub Al-Nughaimshi, the data protection officer, keeps a register: each dataset, its
# classification level and where it may be processed. A dataset marked "in-Kingdom, or outside with an approved
# transfer assessment" may go to the `global` region only when its assessment is approved.
#
# ✏️ **Exercise** · Write `allowed_regions(register, app)`: the set of API regions (`"global"`, `"in-kingdom"`)
# in which **all** datasets of the application may be processed.

# %%
print(register.to_string(index=False))


def allowed_regions(register, app):
    # BEGIN SOLUTION
    rows = register[register.application == app]
    outside = all(r.placement_rule == "any region" or (r.placement_rule.startswith("in-Kingdom, or outside") and r.transfer_assessment.startswith("approved"))
                  for r in rows.itertuples())
    return {"global", "in-kingdom"} if outside else {"in-kingdom"}
    # END SOLUTION


# %%
try:
    placement = {app: sorted(allowed_regions(register, app)) for app in ("anis", "khulasa", "fasil")}
except NotImplementedError:
    placement = M.reference("d3_1_placement")
M.keep("d3_1_placement", placement)
print(placement)

outs = M.outputs()
floors = M.load_json("eval/floors.json")


def worst_language(app, tier):
    tasks = {t["id"]: t for t in M.tasks(app)}
    x = outs[(outs.app == app) & (outs.tier == tier) & (outs.reasoning == "off")]
    return min(np.mean([M.grade(app, tasks[r.task], r.text) for r in x[x.lang == lang].itertuples()]) for lang in ("en", "ar"))


options = pd.DataFrame([
    {"option": "API tier-m, global (October)", "region": "global", "sar_month": N_MONTH * API[("tier-m", "global")], "worst_language": worst_language("khulasa", "tier-m")},
    {"option": "API tier-m, in-Kingdom", "region": "in-kingdom", "sar_month": N_MONTH * API[("tier-m", "in-kingdom")], "worst_language": worst_language("khulasa", "tier-m")},
    {"option": "API tier-s, in-Kingdom", "region": "in-kingdom", "sar_month": N_MONTH * API[("tier-s", "in-kingdom")], "worst_language": worst_language("khulasa", "tier-s")},
    {"option": "Self-hosted, reserved node and operations", "region": "in-kingdom", "sar_month": HOURLY * HOURS, "worst_language": worst_language("khulasa", "local-os")},
])
options["placement_allowed"] = options.region.isin(placement["khulasa"])
options["floor_held"] = options.worst_language >= floors["khulasa"]
print(options.round(3).to_string(index=False))

# %% [markdown]
# ✏️ **Exercise** · Write `recommend(options)`: the name of the cheapest option whose placement is allowed and
# whose floor is held.

# %%
def recommend(options):
    # BEGIN SOLUTION
    ok = options[options.placement_allowed & options.floor_held]
    return ok.sort_values("sar_month").option.iloc[0]
    # END SOLUTION


# %%
try:
    choice = recommend(options)
except NotImplementedError:
    choice = M.reference("d3_1_summary")["recommendation"]
today = options.sar_month.iloc[0]
chosen = options[options.option == choice].iloc[0]
M.keep("d3_1_summary", {"recommendation": choice, "sar_month": round(float(chosen.sar_month), 2), "today_sar_month": round(float(today), 2),
                        "today_allowed": bool(options.placement_allowed.iloc[0]), "self_hosted_sar_month": round(HOURLY * HOURS, 2),
                        "options": options.round(3)})
print(f"\nrecommendation for Khulasa: {choice}, {M.sar(chosen.sar_month)} a month against {M.sar(today)} today, "
      f"and today's placement is {'allowed' if options.placement_allowed.iloc[0] else 'NOT allowed by the register'}")
M.check(choice == "API tier-s, in-Kingdom" and not options.placement_allowed.iloc[0],
        "the register rules out October's placement; the cheapest allowed option that holds the floor is the small tier in the in-Kingdom region")

# %% [markdown]
# 🔍 Two findings for the review, in this order. First: call transcripts were processed outside the Kingdom without
# an approved transfer assessment. That goes to Yaqoub today, whatever it costs. Second: the allowed option that
# holds the floor is also cheaper. That will not always be so: for the dispute agent the in-Kingdom region simply
# costs 30% more, and the open-weight model fails its floor.

# %% [markdown]
# ## ✱ Stretch · One leased hour a night
#
# Summaries are not urgent (Lab 3.2). Lease the node on demand for as many whole hours a night as the day's calls
# need at batch capacity, and compare the month with the API options, with and without the operations cost.

# %%
def stretch():
    # BEGIN SOLUTION
    per_day = N_MONTH / 31
    hours_a_night = math.ceil(per_day / CAP_BATCH)
    node = hours_a_night * 31 * NODE_ON_DEMAND
    print(f"{per_day:,.0f} summaries a day need {hours_a_night} leased hour(s) a night: node {M.sar(node)} a month, "
          f"with operations {M.sar(node + SHEET['operations']['share_of_an_engineer_per_month'])}")
    print(f"against API tier-s in-Kingdom {M.sar(N_MONTH * API[('tier-s', 'in-kingdom')])} and tier-m in-Kingdom {M.sar(N_MONTH * API[('tier-m', 'in-kingdom')])}")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A node at SAR 12 an hour serves 3,000 requests an hour at full load. What does a request cost at 10%
#    utilisation?
#    <details><summary>Answer</summary>SAR 12 over 300 requests: SAR 0.04. At full load it would be SAR 0.004.</details>
# 2. The API price of the tier you use falls by half. What happens to break-even utilisation?
#    <details><summary>Answer</summary>It doubles: the node has to be twice as busy to match the API.</details>
# 3. Self-hosting is cheaper on paper for a dataset the register allows anywhere. What is missing from "on paper"?
#    <details><summary>Answer</summary>The people who run it, the idle hours, the quality of the open-weight model
#    on your tasks, and the latency objective that sets usable capacity.</details>
#
# **Carry forward.** `artifacts/D3_1/break_even.png` and the recommendation are the hosting analysis the capstone
# asks for.
