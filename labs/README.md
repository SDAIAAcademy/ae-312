# AI Cost Engineering and Model Routing: labs

Hands-on notebooks for the SDAIA Academy course **AE-312 AI Cost Engineering and Model Routing (هندسة تكلفة الذكاء الاصطناعي وتوجيه النماذج)**. Every lab works on one month at **Mawj Telecom (موج للاتصالات)**, a fictional operator whose three applications share one model gateway, Maabar: **Anis** (a bilingual care assistant), **Khulasa** (a call-summary job) and **Fasil** (a billing-dispute agent). Each lab starts from a supplied reference state, so none depends on an earlier one.

**The labs need no key, no model on your machine and no accelerator.** They measure a month that has already happened: a usage log, an invoice, recorded model outputs and replayed traffic. A laptop CPU or a Colab CPU runtime is enough. One step, Lab 2.1 step 4, can call a free hosted model when a key is set; without one it uses the supplied outputs and says so.

## Quick start

**Google Colab**
1. Open a notebook from the [course page](https://sdaiaacademy.github.io/ae-312/), or directly: `https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/<notebook>.ipynb`.
2. Run the first cell. It clones this repository and installs `requirements-colab.txt`.

**Local**
```bash
git clone https://github.com/SDAIAAcademy/ae-312
cd ae-312/labs
uv sync                              # creates the environment from pyproject.toml (uv.lock pins every version)
uv run python prepare_data.py --check   # optional: confirms the committed data matches the generator
uv run jupyter lab
```
Run `00_setup_check.ipynb` once before Day 1.

**The optional live step.** Copy `.env.example` to `.env` and paste a free [OpenRouter](https://openrouter.ai/keys) key. Lab 2.1 step 4 then reruns ten tasks against free hosted models (ids ending in `:free`, set in `.env`). Free models change often and have daily request limits: check the ids before a cohort. In Colab, add `OPENROUTER_API_KEY` in the Secrets panel.

## Notebooks

| Day | Session | Notebook | Calls a model |
|---|---|---|---|
| 0 | Setup | [`00_setup_check.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/00_setup_check.ipynb) | no |
| 1 | The token cost model | [`D1_1_cost_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_1_cost_model.ipynb) | no |
| 1 | Agents, retries and long contexts | [`D1_2_expensive_sessions.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_2_expensive_sessions.ipynb) | no |
| 1 | Attribution and showback | [`D1_3_showback.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_3_showback.ipynb) | no |
| 1 | Budgets and limits | [`D1_4_budgets.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_4_budgets.ipynb) | no |
| 2 | Own tasks, several settings | [`D2_1_own_tasks.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_1_own_tasks.ipynb) | step 4, optional |
| 2 | Routing and cascades | [`D2_2_router.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_2_router.ipynb) | no |
| 2 | Prompt layout for prefix caching | [`D2_3_prefix_cache.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_3_prefix_cache.ipynb) | no |
| 2 | Semantic caches and their risks | [`D2_4_semantic_cache.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_4_semantic_cache.ipynb) | no |
| 3 | Self-hosting economics | [`D3_1_break_even.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_1_break_even.ipynb) | no |
| 3 | Batch versus interactive | [`D3_2_batch_tier.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_2_batch_tier.ipynb) | no |
| 3 | Cost per successful outcome | [`D3_3_cost_per_outcome.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_3_cost_per_outcome.ipynb) | no |
| 3 | The cost review | [`D3_4_cost_review.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_4_cost_review.ipynb) | no |

Exercises are marked **✏️ Exercise** and raise `NotImplementedError` until you fill them in. Complete reference versions are in `solutions/`. Every exercise is followed by a check cell with a safety net: when an exercise is not done, the cells below it still run on the reference result from `data/reference/`. Cells marked **✱ Stretch** are optional. Self-checks print ✅ or ❌.

The notebooks are generated from the percent-format sources in `_src/` by `_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions. Edit the sources, not the notebooks.

Labs write their outputs (charts, the review, the capstone scenario) to `artifacts/`, which git ignores. Delete `artifacts/` before running the course's `academy check`, which reports ignored files under `labs/`.

## The case study: Mawj Telecom

Synthetic and deterministic: October 2026, written by `prepare_data.py` with a fixed seed. No real customer, no real personal data, no real provider. The prices are a synthetic sheet in SAR per million tokens.

| Data | File | Contents |
|---|---|---|
| Usage log | `data/usage.csv.gz` | 97,318 requests through the gateway: key, tags, session, step, attempt, status, model tier, input, cached, output and reasoning tokens, latency, language |
| Price sheet | `data/prices.json` | three tiers (`tier-s`, `tier-m`, `tier-l`), cached input, the batch discount, the in-Kingdom premium, the node's hourly price, and the billing rules |
| Invoice | `data/invoice.csv` | twelve lines, SAR 8,242.62: tokens by tier on the gateway's key, a key that bypasses the gateway, the leased node |
| Leased node | `data/gpu_hours.csv` | one row per leased hour: busy minutes and requests served |
| Gateway | `data/gateway/` | keys and teams, the policy of 1 October, a calm day and the incident day to replay |
| Evaluation | `data/eval/` | 100 labelled tasks per application (50 English, 50 Arabic), recorded outputs for three tiers and two reasoning settings, the quality floors |
| Prompts | `data/prompts/` | Anis's instructions and policy sections, two busy hours of requests and 45 quiet-hour requests to replay through a prefix cache |
| Cache traffic | `data/cache/anis_queries.jsonl` | a month of questions with the right answer of each, the customer and whether the answer used account data |
| Hosting | `data/hosting/` | a throughput benchmark of the node, price sheets, the classification register, batch completion times, assumed energy figures, Khulasa's calls |
| Outcomes | `data/outcomes/` | the reviewed outcome of each dispute, and what an escalation and a rework cost |
| Reference results | `data/reference/` | what the reference solution of each exercise measured, for the safety nets and for Lab 3.4 |

## Helpers

`mawj.py` (imported as `M`):

| Helper | What it does |
|---|---|
| `usage()`, `invoice()`, `keys()`, `gpu_hours()`, `prices()`, `tasks(app)`, `outputs()`, `load_json(rel)` | load the files of the case |
| `add_cost(df, region, batch)` | the reference cost model: what the provider bills for each row (Lab 1.1 builds it by hand first) |
| `attribute(df)` | team, application and environment for each row, from keys and tags; what cannot be attributed is `unallocated` |
| `grade(app, task, text)` | the grader in code: the required facts are there and the answer is in the right language |
| `build_prompt`, `first_difference`, `PrefixCache`, `replay_prompts`, `ttft_ms` | a model of a provider's prefix cache: a prefix counts from 1,024 tokens, in steps of 128, and lives 5 minutes |
| `embed(texts)` | a local embedding from hashed character 3-grams, for the semantic cache: no model, no download |
| `chat(tier, system, user, stand_in)` | one call to a free hosted model; returns the stand-in when there is no key or the provider refuses it |
| `add_energy(df)` | watt-hours per row from the assumed figures in `data/hosting/energy.json` |
| `check(condition, message)`, `reference(name)`, `sar(x)`, `lab_dir(name)` | self-checks, safety nets, formatting, the lab's output folder |

`maabar.py` models the gateway: `Gateway(policy).replay(df)` sends a day of the log through budgets (scopes `gateway`, `app`, `env`, `team`, `key`; soft and hard limits per day) and rate limits, and returns a decision for every request. It runs in the notebook. A real gateway keeps this state in a database; the policy file has the same shape of ideas, not the syntax of a product.

**What is modelled and not measured.** The prefix cache, the semantic cache, the batch tier and the gateway are models in Python with the published rules of real ones as parameters. The outputs of the three tiers are recorded and synthetic. The energy figures are assumed. The labs teach the measurement; the numbers describe Mawj, not any provider.

## The capstone

`capstone/README.md` is the brief and the rubric. `capstone/make_scenario.py a|b|c` generates another month at Mawj; set `MAWJ_DATA` to its folder before importing `mawj`. `review/review_template.md` is the two-page template of Lab 3.4.

**Windows and long folder paths.** If an import fails with "The filename or extension is too long", keep the virtual environment in a short folder: set `UV_PROJECT_ENVIRONMENT` to a short path (for example a folder at the root of your drive) before `uv sync`, and run `git config core.longpaths true` in the repository.
