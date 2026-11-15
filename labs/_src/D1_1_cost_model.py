# %% [markdown]
# # Lab 1.1 · A cost model that matches the invoice
#
# Day 1 · Session 1 (The token cost model) · 25 min.
#
# You are the AI cost engineer of Mawj Telecom. Finance has the provider's invoice for October; the gateway,
# Maabar, has a log row for every attempt of every request. You build the cost model that turns the log into the
# invoice: first the model everybody writes, which lands near the invoice for the wrong reasons, then the three
# corrections and the accelerator-hours that make it match line by line, within 2% in total.
#
# **AI policy for this lab: no AI assistance.** The first cost model is yours; the supervised check asks for the same
# arithmetic on paper.
#
# **Reference state.** `data/usage.csv.gz` (the gateway log), `data/prices.json` (the price sheet), `data/invoice.csv`,
# `data/gpu_hours.csv`. All synthetic. The lab needs no earlier lab and no model.
#
# **Tasks**
# - [ ] 1 · Price one request by hand from the price sheet (5')
# - [ ] 2 · The month with a naive model, against the invoice (5')
# - [ ] 3 · Add cached tokens, reasoning tokens and billed failures (7')
# - [ ] 4 · Add the accelerator-hours of the pilot node (4')
# - [ ] 5 · Reconcile line by line and state the gap (4')
# - [ ] ✱ Stretch · Find the spend the gateway never saw

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
P = M.prices()
inv = M.invoice()
u = M.with_register(M.usage())          # adds team, app and env from the key register
tiers = pd.DataFrame(P["tiers"]).T.rename(columns={"input": "p_in", "cached_input": "p_cached", "output": "p_out"})
u = u.merge(tiers, left_on="model", right_index=True, how="left").fillna({"p_in": 0.0, "p_cached": 0.0, "p_out": 0.0})

print(P["rules"]["note"])
print(tiers.to_string())
print(inv.to_string(index=False))
INVOICE_TOKENS = inv[inv.unit == "tokens"].amount_sar.sum()
INVOICE_TOTAL = inv.amount_sar.sum()
print(f"\n{len(u):,} log rows | invoice: {M.sar(INVOICE_TOKENS)} for tokens, {M.sar(INVOICE_TOTAL)} in total")

# %% [markdown]
# ## 1 · Price one request by hand (5')
#
# Prices are in SAR per million tokens. The row below is one answer of Anis, the care assistant: no cached tokens,
# no reasoning tokens, status ok.
#
# ✏️ **Exercise** · Write `price_simple(row)`: input tokens at the input price plus output tokens at the output
# price, in SAR. Do it once on paper first.

# %%
one = u[(u.key_id == "key-anis-prod") & (u.status == "ok")].iloc[0]
print(one[["request_id", "model", "input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens", "p_in", "p_out"]].to_string())


def price_simple(row):
    # BEGIN SOLUTION
    return (row["input_tokens"] * row["p_in"] + row["output_tokens"] * row["p_out"]) / 1e6
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    one_cost = price_simple(one)
except NotImplementedError:
    one_cost = M.reference("d1_1_one_request")
M.keep("d1_1_one_request", one_cost)
print(f"one request of Anis: SAR {one_cost:.5f}  ({one.input_tokens:,} tokens in, {one.output_tokens} out)")
M.check(abs(one_cost - M.add_cost(u[u.request_id == one.request_id]).cost_sar.iloc[0]) < 1e-9, "one request priced as the provider prices it")

# %% [markdown]
# 🔍 The input side is more than 90% of this request's cost. Anis resends about 7,500 tokens of instructions and
# policy text on every turn. Keep that in mind for Lab 2.3.

# %% [markdown]
# ## 2 · The month with a naive model (5')
#
# Apply the same arithmetic to every successful row and compare with the token lines of the invoice.
#
# ✏️ **Exercise** · Write `naive_cost(df)` returning one value per row: the formula of step 1 for rows whose status
# is `ok`, and 0 for the others.

# %%
def naive_cost(df):
    # BEGIN SOLUTION
    c = (df.input_tokens * df.p_in + df.output_tokens * df.p_out) / 1e6
    return c.where(df.status == "ok", 0.0)
    # END SOLUTION


# %%
try:
    naive_total = float(naive_cost(u).sum())
except NotImplementedError:
    naive_total = M.reference("d1_1_naive_total")
M.keep("d1_1_naive_total", naive_total)
print(f"naive model {M.sar(naive_total)} | invoice, token lines {M.sar(INVOICE_TOKENS)} | off by {100 * (naive_total / INVOICE_TOKENS - 1):+.1f}%")
M.check(naive_total > INVOICE_TOKENS, "the naive model lands above the invoice: close, and wrong (step 3 shows why)")

# %% [markdown]
# ## 3 · Cached tokens, reasoning tokens and billed failures (7')
#
# Three facts from the price sheet's rules:
#
# - `input_tokens` **includes** `cached_tokens`, and cached input is billed at the cached price;
# - reasoning tokens are billed as output, and `output_tokens` does **not** include them;
# - the provider bills a request it started to answer, also when the client gave up (`timeout`); it does not bill a
#   request it refused (`error`).
#
# ✏️ **Exercise** · Write `cost_model(df, cached=True, reasoning=True, failures=True)`. Each flag switches one
# correction on, so that the cell after it can show what each one is worth.

# %%
def cost_model(df, cached=True, reasoning=True, failures=True):
    # BEGIN SOLUTION
    cached_tokens = df.cached_tokens if cached else 0
    out_tokens = df.output_tokens + (df.reasoning_tokens if reasoning else 0)
    c = ((df.input_tokens - cached_tokens) * df.p_in + cached_tokens * df.p_cached + out_tokens * df.p_out) / 1e6
    billed = df.status.isin(["ok", "timeout"]) if failures else (df.status == "ok")
    return c.where(billed, 0.0)
    # END SOLUTION


# %%
try:
    ladder = pd.DataFrame([
        {"model": "naive", "sar": cost_model(u, False, False, False).sum()},
        {"model": "+ cached input at the cached price", "sar": cost_model(u, True, False, False).sum()},
        {"model": "+ reasoning tokens as output", "sar": cost_model(u, True, True, False).sum()},
        {"model": "+ billed timeouts", "sar": cost_model(u, True, True, True).sum()},
    ])
    u["cost_sar"] = cost_model(u)
except NotImplementedError:
    ladder = M.reference("d1_1_ladder")
    u["cost_sar"] = M.add_cost(u).cost_sar
ladder["against_invoice_pct"] = (100 * (ladder.sar / INVOICE_TOKENS - 1)).round(2)
M.keep("d1_1_ladder", ladder)
print(ladder.round(2).to_string(index=False))
print("\nCost per request by application (SAR), successful requests only:")
print(u[u.status == "ok"].groupby("app").cost_sar.describe()[["count", "mean", "50%", "max"]].round(4).to_string())
M.check(abs(u.cost_sar.sum() - M.add_cost(u).cost_sar.sum()) < 0.01, "the full model equals the reference cost model")

# %% [markdown]
# 🔍 Read the ladder from top to bottom. The naive model was about 2% off. The cached discount alone moves the
# total **down** by more than a third; reasoning tokens bring most of it back **up**. Two large errors of opposite
# sign hid each other: a model that is close for the wrong reasons breaks the month the traffic mix changes.

# %% [markdown]
# ## 4 · The accelerator-hours of the pilot node (4')
#
# Khulasa's nightly pilot runs on a leased accelerator node. Tokens there are free; the hours are not, used or idle.
# `data/gpu_hours.csv` has one row per leased hour.
#
# ✏️ **Exercise** · Write `node_summary(g, rate)` returning a dictionary with `hours`, `cost_sar`, `requests`,
# `sar_per_request` and `utilisation` (busy minutes over leased minutes).

# %%
g = M.gpu_hours()
RATE = P["local"]["node_sar_per_hour"]


def node_summary(g, rate):
    # BEGIN SOLUTION
    hours = int(g.leased.sum())
    cost = hours * rate
    requests = int(g.requests.sum())
    return {"hours": hours, "cost_sar": cost, "requests": requests, "sar_per_request": cost / requests,
            "utilisation": float(g.busy_minutes.sum() / (hours * 60))}
    # END SOLUTION


# %%
try:
    node = node_summary(g, RATE)
except NotImplementedError:
    node = M.reference("d1_1_node")
M.keep("d1_1_node", node)
# Khulasa's own summaries on the API: rows tagged app=khulasa that did not run on the node. The key register alone
# would also count another team's experiment on the shared key (Lab 1.3).
api_same_job = u[(M.tag(u, "app") == "khulasa") & (u.model != "local-os") & (u.env == "prod")
                 & (u.status == "ok")].cost_sar.mean()
print({k: round(v, 4) for k, v in node.items()})
print(f"a summary on the node: SAR {node['sar_per_request']:.3f} | the same job on the API: SAR {api_same_job:.3f} "
      f"| ratio {node['sar_per_request'] / api_same_job:.0f}x at {100 * node['utilisation']:.0f}% utilisation")
M.check(abs(node["cost_sar"] - inv[inv.provider_key == "node-lease"].amount_sar.sum()) < 0.01, "the node cost equals the lease line of the invoice")

# %% [markdown]
# ## 5 · Reconcile line by line (4')
#
# A total that matches can still hide two lines that are wrong in opposite directions. Reconcile by invoice line:
# model and kind of token.
#
# ✏️ **Exercise** · With DuckDB (or pandas), compute for each hosted model the billed quantities
# `uncached_input`, `cached_input` and `output` (output plus reasoning), over the billed statuses.

# %%
def billed_quantities(u):
    # BEGIN SOLUTION
    return duckdb.sql("""
        select model,
               sum(input_tokens - cached_tokens)          as uncached_input,
               sum(cached_tokens)                         as cached_input,
               sum(output_tokens + reasoning_tokens)      as output
        from u
        where status in ('ok', 'timeout') and model like 'tier-%'
        group by model order by model
    """).df()
    # END SOLUTION


# %%
try:
    q = billed_quantities(u)
except NotImplementedError:
    q = M.reference("d1_1_quantities")
M.keep("d1_1_quantities", q)
mine = q.melt(id_vars="model", var_name="item", value_name="my_quantity")
mine["item"] = mine["item"].map({"uncached_input": "input tokens", "cached_input": "cached input tokens", "output": "output tokens"})
lines = inv[inv.unit == "tokens"].merge(mine, on=["model", "item"], how="left")
lines["my_quantity"] = lines.my_quantity.where(lines.provider_key == "up-maabar-01")     # the log is the gateway's
gateway_lines = lines[lines.provider_key == "up-maabar-01"]
print(lines[["provider_key", "model", "item", "quantity", "my_quantity", "amount_sar"]].to_string(index=False))

model_total = u.cost_sar.sum() + node["cost_sar"]
gap = INVOICE_TOTAL - model_total
print(f"\ncost model {M.sar(model_total)} | invoice {M.sar(INVOICE_TOTAL)} | gap {M.sar(gap)} = {100 * gap / INVOICE_TOTAL:.2f}% of the invoice")
M.keep("d1_1_summary", {"model_total_sar": round(model_total, 2), "invoice_total_sar": round(INVOICE_TOTAL, 2), "gap_pct": round(100 * gap / INVOICE_TOTAL, 2),
                        "hosted_sar": round(u.cost_sar.sum(), 2), "node_sar": node["cost_sar"],
                        "by_app_sar": u.groupby("app").cost_sar.sum().round(2).to_dict()})
M.check((gateway_lines.quantity == gateway_lines.my_quantity).all(), "every line billed to the gateway's key matches the log, token for token")
M.check(abs(gap) / INVOICE_TOTAL <= 0.02, "the cost model reconciles with the invoice within 2%")

# %% [markdown]
# ## ✱ Stretch · The spend the gateway never saw
#
# The gap is small and it is not noise. Which invoice lines have no quantity of yours beside them? What does that
# tell Murtada, who owns the gateway, and Shurooq, who pays the invoice?

# %%
def stretch():
    # BEGIN SOLUTION
    unseen = lines[lines.my_quantity.isna()]
    print(unseen[["provider_key", "model", "item", "quantity", "amount_sar"]].to_string(index=False))
    print(f"{M.sar(unseen.amount_sar.sum())} was billed to a provider key that Maabar never issued: no tags, no budget, no log.")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. Your model sums successful rows only and lands 1% under the invoice in a calm month. What happens to that gap
#    in a month with a provider incident?
#    <details><summary>Answer</summary>It widens: timeouts are billed and they come in bursts. The model was close
#    by luck of the mix, not by construction.</details>
# 2. Why is a summary on the pilot node so much more expensive than on the API, when its tokens are free?
#    <details><summary>Answer</summary>The node is paid by the hour and was busy for a small share of its leased
#    hours. Cost per request is lease cost over requests served: utilisation decides it (Lab 3.1).</details>
# 3. The total reconciles within 2%. Why reconcile by line as well?
#    <details><summary>Answer</summary>Errors of opposite sign cancel in a total. By line, each kind of token has to
#    match, and what does not match has a name: here a provider key outside the gateway.</details>
#
# **Carry forward.** `M.add_cost(df)` is this lab's cost model; every later lab uses it. Nothing is saved.
