# %% [markdown]
# # Lab 3.4 · The two-page cost review
#
# Day 3 · Session 4 (The cost review) · 25 min.
#
# Shurooq Al-Hamli in finance and Murtada Al-Awami on the platform team will read two pages, not eleven notebooks.
# You collect the measured numbers of the three days, put seven candidate options in one table, keep the three
# that hold their quality floor, report energy beside cost, and fill the review template. Then you choose the
# scenario of your capstone and generate its data.
#
# **AI policy: tutor.** An assistant may explain a query or comment on your wording. The ranking, the refusal and
# the two paragraphs in your own words are yours: you defend them without the assistant.
#
# **Reference state.** The results of the reference solutions of Labs 1.1 to 3.3 in `data/reference/`, the usage
# log, and `review/review_template.md`. If your own numbers differ, use yours and say why. All synthetic.
#
# **Tasks**
# - [ ] 1 · Collect the measured numbers of the three days (5')
# - [ ] 2 · Three options: saving, quality effect, risk, energy (8')
# - [ ] 3 · Write the two pages from the template (7')
# - [ ] 4 · Choose the capstone scenario and generate its data (5')
# - [ ] ✱ Stretch · Recompute one savings figure live, as in the defence

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

import time

import pandas as pd

import mawj as M

OUT = M.lab_dir("D3_4")
u = M.add_energy(M.add_cost(M.attribute(M.usage())))
prod = u[u.env == "prod"]
ENERGY = M.load_json("hosting/energy.json")

# %% [markdown]
# ## 1 · Collect the measured numbers (5')
#
# `M.reference(name)` returns what the reference solution of an earlier lab measured.
#
# ✏️ **Exercise** · Write `collect()` returning one dictionary with these keys, each read from the reference named
# beside it:
#
# | key | reference | field |
# |---|---|---|
# | `invoice_sar`, `gap_pct`, `node_sar` | `d1_1_summary` | `invoice_total_sar`, `gap_pct`, `node_sar` |
# | `layout_saving_pct` | `d2_3_summary` | `saving_pct` |
# | `router_saving_pct` | `d2_2_summary` | `saving_per_success_pct` |
# | `semantic_sar_month`, `semantic_wrong_rate` | `d2_4_summary` | `saving_sar_month`, `wrong_rate` |
# | `khulasa_today_sar`, `khulasa_small_sar` | `d3_1_summary` | `today_sar_month`, `sar_month` |
# | `batch_saving_pct` | `d3_2_summary` | `saving_pct` |
# | `full_cost_per_resolved` | `d3_3_full` | the whole dictionary (A and B) |

# %%
def collect():
    # BEGIN SOLUTION
    d11, d31, d24 = M.reference("d1_1_summary"), M.reference("d3_1_summary"), M.reference("d2_4_summary")
    return {"invoice_sar": d11["invoice_total_sar"], "gap_pct": d11["gap_pct"], "node_sar": d11["node_sar"],
            "layout_saving_pct": M.reference("d2_3_summary")["saving_pct"],
            "router_saving_pct": M.reference("d2_2_summary")["saving_per_success_pct"],
            "semantic_sar_month": d24["saving_sar_month"], "semantic_wrong_rate": d24["wrong_rate"],
            "khulasa_today_sar": d31["today_sar_month"], "khulasa_small_sar": d31["sar_month"],
            "batch_saving_pct": M.reference("d3_2_summary")["saving_pct"],
            "full_cost_per_resolved": M.reference("d3_3_full")}
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    n = collect()
except NotImplementedError:
    n = M.reference("d3_4_numbers")
M.keep("d3_4_numbers", n)
for k, v in n.items():
    print(f"  {k:24s} {v}")
M.check(len(n) == 11 and n["gap_pct"] < 2, "eleven measured numbers, and a cost model within 2% of the invoice: without that, none of the others can be trusted")

# %% [markdown]
# ## 2 · Three options: saving, quality effect, risk, energy (8')
#
# Seven candidates came out of the three days. The table below holds, for each, what the month's log says it would
# have saved and what you measured about quality. The quality columns are filled for you from the labs; the
# savings are yours.
#
# ✏️ **Exercise** · Write `savings(n, prod)` returning a dictionary with the saving in SAR a month of each
# candidate:
# - `node`: the leased node, returned;
# - `khulasa_small`: Khulasa on the small tier in the in-Kingdom region, against today;
# - `anis_layout`: the stable prompt layout, as its measured percentage of Anis's production spend;
# - `anis_router`: the router, as its measured percentage of Anis's production spend;
# - `anis_semantic`: the scoped semantic cache;
# - `khulasa_batch`: the batch plan, as its measured percentage of Khulasa **after** the move to the small tier;
# - `fasil_b`: configuration B for every Fasil session: the month's sessions times the difference in model cost
#   per session between A and B (`M.reference("d3_3_by_config")`).

# %%
def savings(n, prod):
    # BEGIN SOLUTION
    anis = prod[prod.app == "anis"].cost_sar.sum()
    cfg = M.reference("d3_3_by_config").set_index("config").per_session
    fasil_sessions = prod[prod.app == "fasil"].session_id.nunique()
    return {"node": n["node_sar"],
            "khulasa_small": n["khulasa_today_sar"] - n["khulasa_small_sar"],
            "anis_layout": anis * n["layout_saving_pct"] / 100,
            "anis_router": anis * n["router_saving_pct"] / 100,
            "anis_semantic": n["semantic_sar_month"],
            "khulasa_batch": n["khulasa_small_sar"] * n["batch_saving_pct"] / 100,
            "fasil_b": fasil_sessions * (cfg["A"] - cfg["B"])}
    # END SOLUTION


# %%
try:
    s = savings(n, prod)
except NotImplementedError:
    s = M.reference("d3_4_savings")
M.keep("d3_4_savings", s)
full = n["full_cost_per_resolved"]
options = pd.DataFrame([
    ("node", "Return the leased node", "none: the pilot never served production", True, "low: revisit at about ten times today's volume"),
    ("anis_layout", "Anis: stable prompt layout", "same words, new order: rerun the 100 tasks before shipping", True, "low: a template change that is easy to revert"),
    ("khulasa_small", "Khulasa: small tier, in-Kingdom region", "94% (English 96, Arabic 92), at the floor of 92 in Arabic", True, "medium: no margin in Arabic; also ends a placement the register does not allow"),
    ("anis_router", "Anis: cascade, Arabic direct to the medium tier", "95% (English 96, Arabic 94), as today", True, "medium: the check misses 10 wrong answers in 100"),
    ("anis_semantic", "Anis: scoped semantic cache at 0.95", f"{n['semantic_wrong_rate']:.1%} wrong answers served from the cache", True, "medium: stale answers after a plan change; needs an expiry"),
    ("khulasa_batch", "Khulasa: batch every 4 hours, urgent calls interactive", "none: same model, later answer", True, "low: summaries arrive hours later, inside the 12-hour need"),
    ("fasil_b", "Fasil: configuration B for every dispute", f"10.5% of resolved disputes wrong against a floor of 6%; SAR {full['B']:.2f} per resolved dispute with people, against {full['A']:.2f}", False, "high: the saving moves to billing operations, doubled"),
], columns=["key", "option", "quality", "holds_floor", "risk"])
options["saving_sar_month"] = options.key.map(s).round(2)
options["share_of_invoice_pct"] = (100 * options.saving_sar_month / n["invoice_sar"]).round(1)
print(options[["option", "saving_sar_month", "share_of_invoice_pct", "holds_floor"]].sort_values("saving_sar_month", ascending=False).to_string(index=False))
M.check(abs(s["node"] - 3472) < 1 and s["fasil_b"] > s["anis_layout"] > s["khulasa_small"] > s["anis_router"],
        "the node is the largest saving, and the second largest on the invoice is configuration B")

# %% [markdown]
# ✏️ **Exercise** · Write `top_three(options)`: the three options with the largest saving **among those that hold
# their floor**, largest first.

# %%
def top_three(options):
    # BEGIN SOLUTION
    return options[options.holds_floor].sort_values("saving_sar_month", ascending=False).head(3)
    # END SOLUTION


# %%
try:
    top = top_three(options)
except NotImplementedError:
    top = options[options.key.isin(M.reference("d3_4_top"))].sort_values("saving_sar_month", ascending=False)
M.keep("d3_4_top", top.key.tolist())
print(top[["option", "saving_sar_month", "quality", "risk"]].to_string(index=False))
M.check(top.key.tolist() == ["node", "anis_layout", "khulasa_small"], "three options that hold their floor; configuration B is not among them")

# %% [markdown]
# 🔍 The three savings are on three different lines of the invoice, so here they do add up. The router and the
# layout both act on Anis's input tokens: their savings would not.

# %% [markdown]
# ### Energy beside cost
#
# `u` carries `energy_wh` for every hosted request, from assumed watt-hours per thousand tokens. The leased node
# draws power for every leased hour, busy or not.
#
# ✏️ **Exercise** · Write `per_thousand(prod)`: one row per production `app` with `requests` (status `ok`),
# `sar_per_1k` and `wh_per_1k` (cost and energy of all rows over successful requests, times 1,000).

# %%
def per_thousand(prod):
    # BEGIN SOLUTION
    g = prod.groupby("app").agg(requests=("status", lambda x: int((x == "ok").sum())), cost=("cost_sar", "sum"), wh=("energy_wh", "sum"))
    g["sar_per_1k"] = 1000 * g.cost / g.requests
    g["wh_per_1k"] = 1000 * g.wh / g.requests
    return g[["requests", "sar_per_1k", "wh_per_1k"]].reset_index()
    # END SOLUTION


# %%
try:
    e = per_thousand(prod)
except NotImplementedError:
    e = M.reference("d3_4_per_thousand")
M.keep("d3_4_per_thousand", e)
e = e[e.app.isin(["anis", "khulasa", "fasil"])]
print(e.round(2).to_string(index=False))

# the three options, in energy: before and after, kWh a month
gpu = M.gpu_hours()
node_kwh = float(gpu.leased.sum() * ENERGY["local"]["node_kw"] * ENERGY["local"]["overhead_factor"])
pilot_requests = int((u.model == "local-os").sum())
kh = prod[prod.app == "khulasa"]
kh_small = M.add_energy(kh.assign(model="tier-s")).energy_wh.sum() / 1000
an = prod[prod.app == "anis"]
an_cached = M.add_energy(an.assign(cached_tokens=(an.input_tokens * M.reference("d2_3_summary")["after"]["cached_share"]).astype(int))).energy_wh.sum() / 1000
energy = pd.DataFrame([("Return the leased node", node_kwh, 0.0), ("Anis: stable prompt layout", an.energy_wh.sum() / 1000, an_cached),
                       ("Khulasa: small tier, in-Kingdom region", kh.energy_wh.sum() / 1000, kh_small)], columns=["option", "kwh_before", "kwh_after"])
print("\n" + energy.round(1).to_string(index=False))
print(f"\nthe node: {node_kwh:,.0f} kWh for {pilot_requests:,} pilot summaries is {1000 * node_kwh / pilot_requests:,.0f} Wh per summary; "
      f"Khulasa on the hosted medium tier: {e.set_index('app').wh_per_1k['khulasa'] / 1000:.2f} Wh per summary")
M.keep("d3_4_energy", energy)
M.check(e.set_index("app").wh_per_1k.idxmax() == "fasil" and node_kwh > kh.energy_wh.sum() / 1000,
        "the agent uses the most energy per thousand requests, and the idle node more than the whole production job")

# %% [markdown]
# 🔍 The option that saves the most money also saves the most energy, for the same reason: an accelerator that is
# leased and idle draws power and bills hours.

# %% [markdown]
# ## 3 · Write the two pages (7')
#
# The template has two places that need your own words. Everything else is filled from the tables above.
#
# ✏️ **Exercise** · Write `my_words()` returning a dictionary with two strings: `decision_asked` (what you ask
# Shurooq and Murtada to decide, with the total and a date) and `not_measured` (at least two things this review
# did not measure).

# %%
def my_words():
    # BEGIN SOLUTION
    total = top.saving_sar_month.sum()
    return {"decision_asked": f"Approve the three actions below for November. Together they take about {M.sar(total)} "
                              f"({100 * total / n['invoice_sar']:.0f}%) off a month like October. We ask for a decision by 15 November, "
                              "and we ask you not to approve configuration B of the dispute agent. Moving Fasil to the in-Kingdom region, "
                              "which the register requires, adds about SAR 755 a month and is not optional.",
            "not_measured": "The quality of Anis's answers with the new prompt order (the 100 tasks must be rerun). "
                            "The energy figures, which are assumed. The saving of the layout outside the two busy hours that were replayed. "
                            "Any live call to a hosted model: every figure comes from the October log and from recorded outputs."}
    # END SOLUTION


# %%
try:
    words, WRITTEN = my_words(), True
except NotImplementedError:
    words, WRITTEN = {"decision_asked": "(write the decision you ask for)", "not_measured": "(write what was not measured)"}, False


def md_table(df):
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(f"{v:,.2f}" if isinstance(v, float) else str(v) for v in row) + " |" for row in df.itertuples(index=False))


show = M.reference("d1_3_showback").groupby("team", as_index=False).cost_sar.sum().sort_values("cost_sar", ascending=False)
show["share_pct"] = 100 * show.cost_sar / show.cost_sar.sum()
unalloc = float(show[show.team == "unallocated"].cost_sar.sum())
inv = M.invoice()
direct = float(inv[inv.provider_key.str.startswith("up-direct")].amount_sar.sum())
refused = options[options.key == "fasil_b"].iloc[0]
values = {
    "month": "October 2026", "to": "Shurooq Al-Hamli (finance), Murtada Al-Awami (platform)", "author": "Elaf Al-Jutaili",
    "invoice_sar": M.sar(n["invoice_sar"]), "gap_pct": n["gap_pct"], "unallocated_sar": M.sar(unalloc), "direct_sar": M.sar(direct),
    "showback_table": md_table(show.rename(columns={"cost_sar": "SAR", "share_pct": "% of spend"})),
    "options_table": md_table(top[["option", "saving_sar_month", "quality", "risk"]].rename(columns={"saving_sar_month": "SAR a month", "quality": "quality, both languages"})),
    "refused": f"**{refused.option}** would take {M.sar(refused.saving_sar_month)} a month off the invoice, more than two of the three options above. "
               f"{refused.quality}. Risk: {refused.risk}.",
    "energy_table": md_table(energy.rename(columns={"kwh_before": "kWh a month, before", "kwh_after": "after"})),
    "not_measured": words["not_measured"], "decision_asked": words["decision_asked"],
    "actions_table": "\n".join(f"| {o} | {owner} | {chk} |" for o, owner, chk in [
        ("Return the leased node", "Qutaiba Al-Ajaji", "the node line is gone from the invoice"),
        ("Anis: stable prompt layout", "Taghreed Al-Omran", "cached share of input above 90%, floor held on the 100 tasks"),
        ("Khulasa: small tier, in-Kingdom region", "Qutaiba Al-Ajaji, with Yaqoub Al-Nughaimshi", "Arabic pass rate at or above 92%, no transcript leaves the Kingdom")]),
}
review = (M.LABS / "review" / "review_template.md").read_text(encoding="utf-8").format_map(values)
(OUT / "review.md").write_text(review, encoding="utf-8")
words_n = len(review.split())
print(review[:1500] + "\n…")
print(f"\nwritten to {(OUT / 'review.md').relative_to(M.LABS).as_posix()}: {words_n} words")
M.check("{" not in review and words_n < 900, "every placeholder is filled and the review fits on two pages (under 900 words)")
if WRITTEN:
    M.check(all(len(w.split()) >= 12 for w in words.values()), "the decision and the list of what was not measured are in your own words")
else:
    print("the two paragraphs in your own words are still to write")

# %% [markdown]
# 🔍 Read the review as Shurooq would: one total, three actions with an owner, one refusal with its reason. Read
# it as Murtada would: every figure names what was measured and what was not.

# %% [markdown]
# ## 4 · Choose the capstone scenario (5')
#
# The capstone is another month at Mawj, generated with other volumes and another seed. Nothing you measured this
# week carries over. Read the three briefs in `capstone/README.md`.
#
# ✏️ **Exercise** · Write `my_scenario()` returning `"a"`, `"b"` or `"c"`.

# %%
def my_scenario():
    # BEGIN SOLUTION
    return "b"
    # END SOLUTION


# %%
try:
    letter = my_scenario()
except NotImplementedError:
    letter = "b"
if M.QUICK:
    print(f"quick mode: scenario {letter} chosen, data not generated")
else:
    done = subprocess.run([sys.executable, "capstone/make_scenario.py", letter], capture_output=True, text=True, encoding="utf-8")
    for line in (done.stdout or done.stderr).splitlines()[:2]:
        print(line)
    print(f"data written to artifacts/capstone/{letter}/data")
    scen = M.read_usage(M.ARTIFACTS / "capstone" / letter / "data" / "usage.csv.gz")
    print(f"{len(scen):,} rows in the scenario's log against {len(u):,} in October's")
    M.check(len(scen) != len(u), "the scenario is another month: its log is not October's")

# %% [markdown]
# 🔍 In your capstone repository, generate the scenario into a `data` folder of your own and set `MAWJ_DATA` to it
# before importing `mawj` (see `capstone/README.md`). There is no reference state there: the checks are yours to
# write.

# %% [markdown]
# ## ✱ Stretch · Recompute one savings figure live
#
# In the defence the assessor picks one figure of your review and you recompute it from the log while they watch.
# Practise on Khulasa: from `M.usage()` alone, recompute what October's production summaries cost and what they
# would cost on the small tier in the in-Kingdom region, and time yourself.

# %%
def stretch():
    # BEGIN SOLUTION
    t0 = time.time()
    k = M.attribute(M.usage())
    k = k[(k.app == "khulasa") & (k.env == "prod") & (k.model != "local-os")]
    today = M.add_cost(k).cost_sar.sum()
    small = M.add_cost(k.assign(model="tier-s"), region="in-kingdom").cost_sar.sum()
    print(f"today {M.sar(today)} | small tier, in-Kingdom {M.sar(small)} | saving {M.sar(today - small)} ({1 - small / today:.0%}) | recomputed in {time.time() - t0:.1f} s")
    print("Lab 3.1 said SAR 838.22 today: it counted the successful summaries only. This figure includes the timeouts that were billed. Say which one your review uses.")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. Two options each save 30% of the same application's spend. What do they save together?
#    <details><summary>Answer</summary>Less than 60%, and it has to be measured with both applied: the second acts
#    on what the first left. Savings on different invoice lines add; savings on the same tokens do not.</details>
# 2. Why does the review name an option it does not recommend?
#    <details><summary>Answer</summary>Because someone will find it on the invoice and propose it. The review
#    shows it was measured and why it fails: the floor, and the cost that moves to people.</details>
# 3. The energy table uses assumed figures. Why report it at all?
#    <details><summary>Answer</summary>It ranks the options and shows the idle node; it is labelled as assumed so
#    nobody quotes it as a measurement. Replace it with the provider's figures when they exist.</details>
#
# **Carry forward.** `artifacts/D3_4/review.md` is the model for the two pages of your capstone, and the scenario
# data is its starting point.
