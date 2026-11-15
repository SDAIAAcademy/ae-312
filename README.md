<!-- academy:title -->
# AI Cost Engineering and Model Routing

هندسة تكلفة الذكاء الاصطناعي وتوجيه النماذج

AI Engineering Track · SDAIA Academy · AE-312 · Level 300

REPLACE: one line under the title: what participants can do after the course

Participants make the cost of language model applications measurable, attributable and smaller without losing quality. For a fictional telecom operator running three applications behind one gateway, a bilingual care assistant, a call-summary job and a billing-dispute agent, they work from a month of synthetic usage traces: they model cost per request and session, attribute spend to teams, set budgets, evaluate model tiers and reasoning settings on their own tasks, route with fallbacks, measure prefix and semantic caches, compare hosted and self-hosted serving and report cost per successful outcome. Cluster capacity planning is AE-307; engine-level optimisation is AE-401.

**Format:** Intensive: 3 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/ae-312/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Compute cost per request and per session from prompt, output and cached tokens, retries, agent steps and accelerator-hours, given a month of usage traces and a synthetic invoice | Applied | a cost model that reconciles with the invoice within 2% |
| LO2 | Configure attribution, budgets and limits per team, application and environment on a model gateway, given three applications sharing one gateway | Applied | a showback table and a replayed spike that trips the hard limit |
| LO3 | Evaluate model tiers, reasoning settings and a routing policy on the operator's own tasks, choosing by cost per successful outcome at a fixed quality floor, given 100 labelled tasks per application | Performance | a results table and a router configuration with its measured savings |
| LO4 | Measure how prefix and semantic caching change cost, latency and answer correctness, including isolation between customers, given replayed traffic for the care assistant | Applied | hit rates, a wrong-answer rate and a passing cross-customer isolation test |
| LO5 | Decide between hosted APIs and a self-hosted open-weight model with a break-even analysis that includes utilisation and data-placement rules, given price sheets, a throughput benchmark and the operator's classification register | Performance | a break-even chart and a recommendation |
| LO6 | Deliver a cost review with three measured savings options to engineering and finance stakeholders, given an unseen capstone scenario | Performance | a notebook and a two-page review reporting energy beside cost, defended in ten minutes |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Where the money goes | The token cost model; Agents, retries and long contexts; Attribution and showback; Budgets and limits | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Route and cache | Own tasks, several settings; Routing and cascades; Prompt layout for prefix caching; Semantic caches and their risks | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Host or buy, and report | Self-hosting economics; Batch versus interactive; Cost per successful outcome; The cost review | [`slides/day3.html`](slides/day3.html) |
| Capstone | Capstone project presentations |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Compute cost per request for the three applications and reconcile it with the synthetic invoice | [`D1_1_compute_cost_per.ipynb`](labs/D1_1_compute_cost_per.ipynb) |
| 1.2 | Day 1 · Session 2 | Find the ten most expensive sessions and attribute their cost to steps, retries and context growth | [`D1_2_find_ten_most.ipynb`](labs/D1_2_find_ten_most.ipynb) |
| 1.3 | Day 1 · Session 3 | Tag spend by team, application and environment through gateway keys and produce a showback table | [`D1_3_tag_spend_team.ipynb`](labs/D1_3_tag_spend_team.ipynb) |
| 1.4 | Day 1 · Session 4 | Set soft and hard budgets per application and trip the hard limit with a replayed spike | [`D1_4_set_soft_hard.ipynb`](labs/D1_4_set_soft_hard.ipynb) |
| 2.1 | Day 2 · Session 1 | Score supplied outputs of three model tiers at two reasoning settings on 100 tasks for quality, latency and cost, and rerun ten tasks live to check them | [`D2_1_score_supplied_outputs.ipynb`](labs/D2_1_score_supplied_outputs.ipynb) |
| 2.2 | Day 2 · Session 2 | Build a two-tier router with a quality check and fallback and measure cost per successful outcome | [`D2_2_build_two_tier.ipynb`](labs/D2_2_build_two_tier.ipynb) |
| 2.3 | Day 2 · Session 3 | Move stable content to the front of a prompt and measure the cache hit rate and cost | [`D2_3_move_stable_content.ipynb`](labs/D2_3_move_stable_content.ipynb) |
| 2.4 | Day 2 · Session 4 | Add a semantic cache, measure hit and wrong-answer rates and test that no answer crosses customers | [`D2_4_add_semantic_cache.ipynb`](labs/D2_4_add_semantic_cache.ipynb) |
| 3.1 | Day 3 · Session 1 | Fill a cost model for serving an open-weight model and find break-even utilisation against API prices | [`D3_1_fill_cost_model.ipynb`](labs/D3_1_fill_cost_model.ipynb) |
| 3.2 | Day 3 · Session 2 | Move the call-summary job to a batch tier and recompute cost and turnaround | [`D3_2_move_call_summary.ipynb`](labs/D3_2_move_call_summary.ipynb) |
| 3.3 | Day 3 · Session 3 | Join cost with evaluation outcomes and report cost per resolved dispute | [`D3_3_join_cost_evaluation.ipynb`](labs/D3_3_join_cost_evaluation.ipynb) |
| 3.4 | Day 3 · Session 4 | Draft a two-page review with three measured savings options, then choose the capstone scenario | [`D3_4_draft_two_page.ipynb`](labs/D3_4_draft_two_page.ipynb) |
<!-- /academy:labs -->

## Capstone

A cost review of an unseen scenario: a public repository with the notebook, measured routing and caching results and a two-page memo with three savings options, defended in ten minutes

**Submission:** REPLACE: what participants submit and how: a public repository link, or a shared folder for a course without code

## Prerequisites

- AE-203 Building Applications on Language Models
- AE-205 Deploying AI Services: Containers, Serving and Monitoring
- Groups and joins usage logs with SQL or dataframes
- Has run an evaluation set against a language model application

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Model gateway with budgets and routing:** LiteLLM, Agent Router
- **Language model access:** a locally served open-weight model, a free hosted open-weight model, any commercial API
- **Evaluation harness:** promptfoo, Inspect
- **Usage analysis:** DuckDB, pandas
- **Cache stores:** Valkey, PostgreSQL with pgvector
- **Local inference server:** vLLM, llama.cpp
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- NDMO Data Classification Policy: REPLACE: the address of the official text
- Personal Data Protection Law and its implementing regulations, including the transfer regulation: REPLACE: the address of the official text
- SDAIA AI Adoption Framework: REPLACE: the address of the official text
- SDAIA AI Ethics Principles: REPLACE: the address of the official text
