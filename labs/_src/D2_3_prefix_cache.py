# %% [markdown]
# # Lab 2.3 · Prompt layout for prefix reuse
#
# Day 2 · Session 3 (Prompt layout for prefix caching) · 25 min.
#
# Anis sends about 8,400 tokens per request and the log of October shows no cached token at all. A provider reuses
# a prompt only as far as it is identical to an earlier one **from the first token**. You replay two busy hours of
# the assistant through a model of a prefix cache, find the three things that break the shared prefix, reorder the
# prompt and measure hit rate, cost and time to first token before and after.
#
# **AI policy: tutor.** An assistant may explain the helper functions. The diagnosis and the layout are yours.
#
# **Reference state.** `data/prompts/anis_replay.jsonl.gz` (2,219 requests of two evening hours),
# `data/prompts/anis_instructions.md`, `data/prompts/policy_sections.json`. The cache is `M.PrefixCache`: a prefix
# counts from 1,024 tokens, in steps of 128, and lives 5 minutes after its last use. No model is called.
#
# **Tasks**
# - [ ] 1 · Replay the current layout through the prefix cache (5')
# - [ ] 2 · Find what breaks the prefix (5')
# - [ ] 3 · Reorder: stable first, variable last (8')
# - [ ] 4 · Hit rate, cost and time to first token, before and after (7')
# - [ ] ✱ Stretch · A quiet period: when does a cache with a write premium lose money?

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

import pandas as pd

import mawj as M

# %%
reqs = M.read_jsonl(M.DATA / "prompts" / "anis_replay.jsonl.gz")
print(f"{len(reqs):,} requests in {reqs[-1]['t'] / 3600:.1f} hours | current layout: {M.CURRENT_LAYOUT}")
for part in M.CURRENT_LAYOUT:
    print(f"  {part:13s} {M.count_tokens(M.render_part(reqs[40], part)):6,d} tokens")
print("\n" + M.build_prompt(reqs[40])[:260].replace("\n", " ⏎ "))

# %% [markdown]
# ## 1 · Replay the current layout (5')
#
# `M.replay_prompts(reqs, layout, sort_policies)` sends every request through the cache and returns one row per
# request with `input_tokens` and `cached_tokens`.
#
# ✏️ **Exercise** · Write `summarise(r)` returning a dictionary: `hit_rate` (share of requests with any cached
# token), `cached_share` (cached tokens over input tokens), `cost_sar` (with `M.add_cost`) and `ttft_ms` (median
# of `M.ttft_ms(r)`, the time to first token).

# %%
def summarise(r):
    # BEGIN SOLUTION
    return {"hit_rate": float((r.cached_tokens > 0).mean()), "cached_share": float(r.cached_tokens.sum() / r.input_tokens.sum()),
            "cost_sar": float(M.add_cost(r).cost_sar.sum()), "ttft_ms": float(M.ttft_ms(r).median())}
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
def _summarise(r):
    try:
        return summarise(r)
    except NotImplementedError:
        return {"hit_rate": float((r.cached_tokens > 0).mean()), "cached_share": float(r.cached_tokens.sum() / r.input_tokens.sum()),
                "cost_sar": float(M.add_cost(r).cost_sar.sum()), "ttft_ms": float(M.ttft_ms(r).median())}


before = _summarise(M.replay_prompts(reqs))
print({k: round(v, 3) for k, v in before.items()})
M.check(before["hit_rate"] == 0.0, "with the current layout no request reuses anything: 0% of 2,219 requests")

# %% [markdown]
# ## 2 · Find what breaks the prefix (5')
#
# `M.first_difference(a, b)` returns the token index at which two prompts stop being equal, and the text around
# that place in each.
#
# ✏️ **Exercise** · Write `where_they_differ(a, b, layout, sort_policies=False)`: build the prompts of requests `a`
# and `b` with `M.build_prompt` and return what `M.first_difference` gives.

# %%
def where_they_differ(a, b, layout, sort_policies=False):
    # BEGIN SOLUTION
    return M.first_difference(M.build_prompt(a, layout, sort_policies), M.build_prompt(b, layout, sort_policies))
    # END SOLUTION


# %%
def _where(a, b, layout, sort_policies=False):
    try:
        return where_they_differ(a, b, layout, sort_policies)
    except NotImplementedError:
        return M.first_difference(M.build_prompt(a, layout, sort_policies), M.build_prompt(b, layout, sort_policies))


a, b = reqs[40], reqs[41]            # two requests of different customers, seconds apart
tries = [("the current layout", M.CURRENT_LAYOUT, False),
         ("the clock moved to the end", ["profile", "instructions", "policies", "history", "question", "clock"], False),
         ("then the profile after the policies", ["instructions", "policies", "profile", "history", "question", "clock"], False),
         ("then the policy sections sorted", ["instructions", "policies", "profile", "history", "question", "clock"], True)]
found = []
for name, layout, srt in tries:
    n, ta, tb = _where(a, b, layout, srt)
    found.append({"layout": name, "equal_up_to_token": n})
    print(f"{name}: equal up to token {n:,}\n    a: …{ta}\n    b: …{tb}")
M.keep("d2_3_breakers", found)
M.check(found[0]["equal_up_to_token"] < 20 and found[1]["equal_up_to_token"] < 20 < found[2]["equal_up_to_token"] < found[3]["equal_up_to_token"],
        "today two prompts differ in their first line; after three fixes they are equal for thousands of tokens")

# %% [markdown]
# 🔍 Three breakers, in the order you met them: a clock with seconds in the first line, the customer's profile before
# the instructions, and policy sections in a different order on every request (the application builds the pack
# from a set). The third one is invisible in a code review of the prompt template.

# %% [markdown]
# ## 3 · Reorder: stable first, variable last (8')
#
# The rule: what is the same for every request goes first, then what is the same within a conversation, then what
# changes on every request.
#
# ✏️ **Exercise** · Write `stable_layout()` returning `(layout, sort_policies)`: the order of the six parts
# (`clock`, `profile`, `instructions`, `policies`, `history`, `question`) and whether the policy sections are
# sorted.

# %%
def stable_layout():
    # BEGIN SOLUTION
    return ["instructions", "policies", "profile", "history", "question", "clock"], True
    # END SOLUTION


# %%
try:
    LAYOUT, SORT = stable_layout()
except NotImplementedError:
    LAYOUT, SORT = ["instructions", "policies", "profile", "history", "question", "clock"], True
replayed = M.replay_prompts(reqs, LAYOUT, SORT)
after = _summarise(replayed)
print({k: round(v, 3) for k, v in after.items()})
M.check(sorted(LAYOUT) == sorted(M.CURRENT_LAYOUT), "the new layout holds the same six parts: nothing was dropped from the prompt")
M.check(after["cached_share"] > 0.9, f"more than 90% of input tokens are now read from the cache ({after['cached_share']:.1%})")

# %% [markdown]
# 🔍 Within a conversation the history is a stable prefix too: turn 2 extends turn 1. That only works when the
# profile comes before the history and the clock after the question.

# %% [markdown]
# ## 4 · Before and after (7')
#
# ✏️ **Exercise** · Write `compare(before, after)`: a frame with one row per metric (`hit_rate`, `cached_share`,
# `cost_sar`, `ttft_ms`) and the columns `before`, `after` and `change_pct` (after against before, in percent;
# leave it empty where before is 0).

# %%
def compare(before, after):
    # BEGIN SOLUTION
    t = pd.DataFrame({"before": before, "after": after})
    t["change_pct"] = (100 * (t.after / t.before - 1)).where(t.before != 0)
    return t
    # END SOLUTION


# %%
try:
    table = compare(before, after)
except NotImplementedError:
    table = M.reference("d2_3_compare").set_index("metric")
M.keep("d2_3_compare", table.rename_axis("metric").reset_index())
print(table.round(3).to_string())
saving = 1 - after["cost_sar"] / before["cost_sar"]
anis_month = 911.32
print(f"\ncost of the two hours: {M.sar(before['cost_sar'])} before, {M.sar(after['cost_sar'])} after: {saving:.0%} less. "
      f"On Anis's October bill of {M.sar(anis_month)} that is about {M.sar(anis_month * saving)} a month, if the month behaves like these two busy hours.")
M.keep("d2_3_summary", {"before": before, "after": after, "saving_pct": round(100 * saving, 1)})
M.check(saving > 0.7 and after["ttft_ms"] < before["ttft_ms"], "the new layout costs less and answers sooner, with the same words in the prompt")

# %% [markdown]
# 🔍 The quality of the answers has not been measured here. The model reads the same text in another order: rerun
# the 100 tasks of Lab 2.1 with the new layout before it ships. A saving that has not passed the floor is not a
# saving yet.

# %% [markdown]
# ## ✱ Stretch · A quiet period
#
# Some providers charge more for the tokens they write into the cache: 1.25 times the input price for an entry
# that lives 5 minutes, 2 times for one that lives an hour (the published terms of one large provider). Replay
# `data/prompts/anis_replay_quiet.jsonl`, 45 requests arriving several minutes apart, with the stable layout, under
# three terms: no cache, 5 minutes at 1.25, one hour at 2. Which one is cheapest?

# %%
def stretch():
    # BEGIN SOLUTION
    quiet = M.read_jsonl(M.DATA / "prompts" / "anis_replay_quiet.jsonl")
    p = M.prices()["tiers"]["tier-m"]
    for name, ttl, write in (("no cache", 0, 1.0), ("5 minutes, writes at 1.25", 300, 1.25), ("one hour, writes at 2", 3600, 2.0)):
        r = M.replay_prompts(quiet, LAYOUT, SORT, cache=M.PrefixCache(ttl_s=ttl))
        written = r.written_tokens if ttl else 0
        cost = ((r.input_tokens - r.cached_tokens - written) * p["input"] + written * p["input"] * write
                + r.cached_tokens * p["cached_input"] + r.output_tokens * p["output"]).sum() / 1e6
        print(f"{name:28s} hit rate {float((r.cached_tokens > 0).mean()):4.0%} | {M.sar(cost, 3)}")
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A prompt starts with "Current time:" and the time in seconds. How much of it can a prefix cache reuse?
#    <details><summary>Answer</summary>Nothing: the first tokens differ on every request, so no prefix is shared.
#    Put the time at the end, or give the date only.</details>
# 2. The template is in the right order and the hit rate is still low. Name one cause the template does not show.
#    <details><summary>Answer</summary>Content assembled in a varying order (a set, a dictionary, retrieved passages
#    ranked differently), or a tool list that changes. Compare two real prompts token by token.</details>
# 3. Traffic drops to one request every eight minutes at night. What happens to the hit rate?
#    <details><summary>Answer</summary>Entries expire between requests, so most requests miss. Where writes cost a
#    premium, caching can then cost more than it saves.</details>
#
# **Carry forward.** The stable layout and its measured saving go into the review of Lab 3.4.
