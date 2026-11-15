# %% [markdown]
# # Lab 2.1 · Three tiers, two reasoning settings, your own tasks
#
# Day 2 · Session 1 (Own tasks, several settings) · 25 min.
#
# A public leaderboard does not know Mawj's plans or its customers' Arabic. You score the supplied outputs of three
# model tiers at two reasoning settings on 100 labelled tasks of the care assistant, for quality, latency and cost,
# apply the quality floor in each language, and rerun ten tasks against a live model to check the supplied results.
#
# **AI policy: tutor.** An assistant may explain pandas syntax. The grader and the choice are yours.
#
# **Reference state.** `data/eval/tasks_anis.jsonl` (100 tasks, 50 in English and 50 in Arabic),
# `data/eval/outputs.jsonl.gz` (supplied outputs with token counts and latency; **synthetic**), `data/eval/floors.json`.
# Step 4 calls a free hosted model when `OPENROUTER_API_KEY` is set and uses the supplied outputs otherwise.
#
# **Tasks**
# - [ ] 1 · A grader for the care assistant (6')
# - [ ] 2 · Score six configurations: quality, latency, cost (7')
# - [ ] 3 · Split by language and apply the quality floor (5')
# - [ ] 4 · Rerun ten tasks live and compare (7')
# - [ ] ✱ Stretch · The same table for the call-summary job and the dispute agent

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
TASKS = {t["id"]: t for t in M.tasks("anis")}
FLOOR = M.load_json("eval/floors.json")["anis"]
outs = M.outputs()
o = M.add_cost(outs[(outs.app == "anis") & outs.tier.isin(M.TIERS)].rename(columns={"tier": "model"})).rename(columns={"model": "tier"})
one = TASKS["A-ar-01"]
print(one["question"], "| expected:", one["expected"])
print(o[o.task == "A-ar-01"][["tier", "reasoning", "status", "text"]].to_string(index=False))
print(f"\n{len(TASKS)} tasks | {len(o)} supplied outputs | floor {FLOOR:.0%} in each language | live model: {M.live()}")

# %% [markdown]
# ## 1 · A grader for the care assistant (6')
#
# An answer of Anis passes when it holds every fact the task expects **and** is written in the customer's language.
# `task["expected"]` has `must_include` (strings that must appear) and `lang`. `M.language_of(text)` returns `"ar"`
# or `"en"`.
#
# ✏️ **Exercise** · Write `grade_anis(task, text)` returning `True` or `False`. An empty answer fails.

# %%
def grade_anis(task, text):
    # BEGIN SOLUTION
    exp = task["expected"]
    if not text:
        return False
    return all(s in text + " " for s in exp["must_include"]) and M.language_of(text) == exp["lang"]
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    o["passed"] = [grade_anis(TASKS[r.task], r.text) for r in o.itertuples()]
except NotImplementedError:
    o["passed"] = [M.grade("anis", TASKS[r.task], r.text) for r in o.itertuples()]
reference_grade = [M.grade("anis", TASKS[r.task], r.text) for r in o.itertuples()]
print(f"passed {int(o.passed.sum())} of {len(o)} outputs")
M.check(list(o.passed) == reference_grade, "your grader agrees with the reference grader on all 600 outputs")

# %% [markdown]
# 🔍 Read three failures of `tier-s` in Arabic before you count anything:
# `o[(o.tier == "tier-s") & (o.lang == "ar") & ~o.passed].text.head(8)`. Which ones could a program notice without
# knowing the right answer? Lab 2.2 depends on that.

# %% [markdown]
# ## 2 · Score six configurations (7')
#
# ✏️ **Exercise** · Write `score(o)`: one row per `tier` and `reasoning` with `pass_rate`, `p50_latency_s`
# (median latency of the answers, in seconds) and `sar_per_task` (mean `cost_sar`; an errored call costs 0 and
# fails).

# %%
def score(o):
    # BEGIN SOLUTION
    return o.groupby(["tier", "reasoning"]).agg(pass_rate=("passed", "mean"),
                                                p50_latency_s=("latency_ms", lambda x: x.median() / 1000),
                                                sar_per_task=("cost_sar", "mean")).reset_index()
    # END SOLUTION


# %%
try:
    table = score(o)
except NotImplementedError:
    table = M.reference("d2_1_table")
M.keep("d2_1_table", table)
print(table.round(4).to_string(index=False))
M.check(len(table) == 6 and table.pass_rate.between(0, 1).all(), "six configurations scored")

# %% [markdown]
# 🔍 What does the high reasoning setting buy on this task, and what does it cost in SAR and in seconds? A care
# answer is a lookup in a plan sheet. Keep the question for the dispute agent in the stretch.

# %% [markdown]
# ## 3 · Split by language and apply the floor (5')
#
# The floor is 92% **in each language**. An average over both can hide a language that fails.
#
# ✏️ **Exercise** · Write `by_language(o)`: one row per `tier` and `reasoning` with the columns `en` and `ar`
# (pass rates), `worst` (the lower of the two) and `meets_floor`.

# %%
def by_language(o, floor=FLOOR):
    # BEGIN SOLUTION
    t = o.pivot_table(index=["tier", "reasoning"], columns="lang", values="passed", aggfunc="mean").reset_index()
    t["worst"] = t[["en", "ar"]].min(axis=1)
    t["meets_floor"] = t.worst >= floor
    return t[["tier", "reasoning", "en", "ar", "worst", "meets_floor"]]
    # END SOLUTION


# %%
try:
    lang = by_language(o)
except NotImplementedError:
    lang = M.reference("d2_1_by_language")
M.keep("d2_1_by_language", lang)
full = table.merge(lang, on=["tier", "reasoning"])
print(full.round(4).to_string(index=False))
choice = full[full.meets_floor].sort_values("sar_per_task").iloc[0]
M.keep("d2_1_choice", {"tier": choice.tier, "reasoning": choice.reasoning, "sar_per_task": round(float(choice.sar_per_task), 5),
                       "en": float(choice.en), "ar": float(choice.ar)})
print(f"\ncheapest configuration that keeps the floor in both languages: {choice.tier}, reasoning {choice.reasoning}, SAR {choice.sar_per_task:.4f} a task")
small = full[(full.tier == "tier-s") & (full.reasoning == "off")].iloc[0]
M.check(bool(small.en >= FLOOR and small.ar < FLOOR), f"the small tier keeps the floor in English ({small.en:.0%}) and fails it in Arabic ({small.ar:.0%})")
M.check(choice.tier == "tier-m" and choice.reasoning == "off", "the choice is the medium tier without reasoning")

# %% [markdown]
# 🔍 With 50 tasks per language one task is 2 points. A configuration at 94% and one at 92% differ by one task:
# do not rank on that. The floor is a decision of the application's owner, set before the prices are compared.

# %% [markdown]
# ## 4 · Rerun ten tasks live and compare (7')
#
# Supplied outputs are a recording. Before you build on a recording, check a sample of it against a live model.
# `M.chat(tier, system, user, stand_in=row)` calls the free hosted model that plays the tier; without a key it
# returns the supplied output and says so in `source`.
#
# ✏️ **Exercise** · Write `rerun(task, tier)`: build the user message from the task's `context` and `question`,
# call `M.chat` with the supplied output of that task and tier (reasoning off) as `stand_in`, grade the answer, and
# return a dictionary with `task`, `source`, `passed_live` and `passed_supplied`.

# %%
SYSTEM = ("You are Anis, the care assistant of Mawj Telecom. Answer in the language of the customer's question, "
          "in one sentence, using only the plan sheet. Quote amounts with Western digits.")
SAMPLE = [f"A-{lang}-{i:02d}" for lang in ("en", "ar") for i in M.pick((3, 11, 20, 34, 47), (3, 20))]


def supplied(task_id, tier):
    return o[(o.task == task_id) & (o.tier == tier) & (o.reasoning == "off")].iloc[0].to_dict()


def rerun(task, tier="tier-m"):
    # BEGIN SOLUTION
    row = supplied(task["id"], tier)
    reply = M.chat(tier, SYSTEM, task["context"] + "\n\nCustomer: " + task["question"], stand_in=row)
    return {"task": task["id"], "source": reply["source"], "passed_live": M.grade("anis", task, reply["text"]),
            "passed_supplied": bool(row["passed"])}
    # END SOLUTION


# %%
try:
    live = pd.DataFrame([rerun(TASKS[t]) for t in SAMPLE])
except NotImplementedError:
    live = M.reference("d2_1_live")
M.keep("d2_1_live", live)
print(live.to_string(index=False))
agreement = float((live.passed_live == live.passed_supplied).mean())
sources = sorted(set(live.source))
print(f"\nsource: {sources} | agreement with the supplied results on {len(live)} tasks: {agreement:.0%}")
if sources == ["stand-in"]:
    print("No live model was called: this compared the supplied outputs with themselves. Set OPENROUTER_API_KEY to run the check for real.")
M.check(len(live) == len(SAMPLE), f"{len(SAMPLE)} tasks rerun")

# %% [markdown]
# 🔍 A free hosted model is not the provider's tier: the live step checks the **method** (prompt, grader, task),
# not the supplied pass rates. When live and supplied disagree, read the answer before you blame either.

# %% [markdown]
# ## ✱ Stretch · The other two applications
#
# Score the call-summary job and the dispute agent the same way with the reference grader `M.grade(app, task, text)`
# and their floors. Which application runs on a tier it does not need? For which one does reasoning pay?

# %%
def stretch():
    # BEGIN SOLUTION
    floors = M.load_json("eval/floors.json")
    for app in ("khulasa", "fasil"):
        tasks = {t["id"]: t for t in M.tasks(app)}
        x = M.add_cost(outs[(outs.app == app) & outs.tier.isin(M.TIERS)].rename(columns={"tier": "model"})).rename(columns={"model": "tier"})
        x["passed"] = [M.grade(app, tasks[r.task], r.text) for r in x.itertuples()]
        t = score(x).merge(by_language(x, floors[app]), on=["tier", "reasoning"])
        print(f"\n{app} (floor {floors[app]:.0%})")
        print(t.round(4).to_string(index=False))
    # END SOLUTION


try:
    stretch()
except NotImplementedError:
    print("✱ Stretch: not done yet")

# %% [markdown]
# ## Checkpoint
#
# 1. A configuration scores 95% overall: 100% in English and 90% in Arabic. The floor is 92%. Does it pass?
#    <details><summary>Answer</summary>No. The floor holds in each language; six in ten of the assistant's
#    customers write in Arabic.</details>
# 2. Why score your own tasks when public benchmarks exist?
#    <details><summary>Answer</summary>A benchmark measures tasks that are not yours, in a mix that is not yours.
#    The choice between two tiers is decided by a few points on your tasks.</details>
# 3. The high reasoning setting raised the pass rate by one task and the cost by 30%. What do you report?
#    <details><summary>Answer</summary>Both numbers, and that one task of fifty is inside the noise. On this task
#    reasoning is not worth its cost; on the dispute agent it is.</details>
#
# **Carry forward.** Lab 2.2 starts from the same supplied outputs. Nothing is saved here.
