<!-- academy:title -->
# AI Cost Engineering and Model Routing

هندسة تكلفة الذكاء الاصطناعي وتوجيه النماذج

AI Engineering Track · SDAIA Academy · AE-312 · Level 300

Make the cost of language model applications measurable, attributable and smaller, without losing quality

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
| Capstone | Capstone: the cost review, defended |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | A cost model that matches the invoice | [`D1_1_cost_model.ipynb`](labs/D1_1_cost_model.ipynb) |
| 1.2 | Day 1 · Session 2 | The ten most expensive sessions | [`D1_2_expensive_sessions.ipynb`](labs/D1_2_expensive_sessions.ipynb) |
| 1.3 | Day 1 · Session 3 | A showback table from gateway keys | [`D1_3_showback.ipynb`](labs/D1_3_showback.ipynb) |
| 1.4 | Day 1 · Session 4 | Soft and hard budgets, and a spike | [`D1_4_budgets.ipynb`](labs/D1_4_budgets.ipynb) |
| 2.1 | Day 2 · Session 1 | Three tiers, two reasoning settings, your own tasks | [`D2_1_own_tasks.ipynb`](labs/D2_1_own_tasks.ipynb) |
| 2.2 | Day 2 · Session 2 | A two-tier router with a quality check | [`D2_2_router.ipynb`](labs/D2_2_router.ipynb) |
| 2.3 | Day 2 · Session 3 | Prompt layout for prefix reuse | [`D2_3_prefix_cache.ipynb`](labs/D2_3_prefix_cache.ipynb) |
| 2.4 | Day 2 · Session 4 | A semantic cache and its wrong answers | [`D2_4_semantic_cache.ipynb`](labs/D2_4_semantic_cache.ipynb) |
| 3.1 | Day 3 · Session 1 | Break-even utilisation for self-hosting | [`D3_1_break_even.ipynb`](labs/D3_1_break_even.ipynb) |
| 3.2 | Day 3 · Session 2 | The call-summary job on a batch tier | [`D3_2_batch_tier.ipynb`](labs/D3_2_batch_tier.ipynb) |
| 3.3 | Day 3 · Session 3 | Cost per resolved dispute | [`D3_3_cost_per_outcome.ipynb`](labs/D3_3_cost_per_outcome.ipynb) |
| 3.4 | Day 3 · Session 4 | The two-page cost review | [`D3_4_cost_review.ipynb`](labs/D3_4_cost_review.ipynb) |
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

### Cost models, allocation and unit economics

- [FinOps Foundation: FinOps for AI overview](https://www.finops.org/wg/finops-for-ai-overview/)
- [FinOps Foundation: GenAI FinOps, how token pricing really works](https://www.finops.org/wg/genai-finops-how-token-pricing-really-works/)
- [FOCUS, the FinOps Open Cost and Usage Specification](https://focus.finops.org/)

### Gateways, budgets and routing

- [LiteLLM documentation: budgets and rate limits](https://docs.litellm.ai/docs/proxy/users)
- [LiteLLM documentation: fallbacks](https://docs.litellm.ai/docs/proxy/reliability)
- [LiteLLM documentation: spend tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)
- [Chen, Zaharia, Zou (2023): FrugalGPT](https://arxiv.org/abs/2305.05176)
- [Ong and others (2024): RouteLLM, learning to route LLMs with preference data](https://arxiv.org/abs/2406.18665)
- [OpenRouter: models, with the free hosted ones](https://openrouter.ai/models)

### Caching and batch tiers

- [Claude Platform documentation: prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [OpenAI documentation: prompt caching](https://platform.openai.com/docs/guides/prompt-caching)
- [Claude Platform documentation: batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [GPTCache, an open-source semantic cache](https://github.com/zilliztech/GPTCache)
- [Valkey](https://valkey.io/)
- [pgvector](https://github.com/pgvector/pgvector)

### Serving, evaluation, analysis and energy

- [vLLM documentation](https://docs.vllm.ai/en/latest/)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [promptfoo documentation](https://www.promptfoo.dev/docs/intro/)
- [Inspect, an evaluation framework](https://inspect.aisi.org.uk/)
- [DuckDB documentation](https://duckdb.org/docs/stable/)
- [Elsworth and others (2025): Measuring the environmental impact of delivering AI at Google scale](https://arxiv.org/abs/2508.15734)

### National references

- [Data Classification Policy (National Data Management Office)](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf)
- [Personal Data Protection Law](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf)
- [Implementing Regulation of the Personal Data Protection Law](https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf)
- [Regulation on Personal Data Transfer Outside the Kingdom](https://sdaia.gov.sa/Documents/RegulationonPersonalDataEN.pdf)
- [AI Adoption Framework](https://sdaia.gov.sa/en/SDAIA/about/Files/AIAdoptionFramework.pdf)
- [Principles of AI Ethics](https://sdaia.gov.sa/en/SDAIA/about/Documents/ai-principles.pdf)
<!-- /academy:sources -->

### National references

- NDMO Data Classification Policy: REPLACE: the address of the official text
- Personal Data Protection Law and its implementing regulations, including the transfer regulation: REPLACE: the address of the official text
- SDAIA AI Adoption Framework: REPLACE: the address of the official text
- SDAIA AI Ethics Principles: REPLACE: the address of the official text
