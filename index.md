---
course: "AI Cost Engineering and Model Routing"
code: "AE-312"
version: "2027.1.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-312/index.html"
---

# AI Cost Engineering and Model Routing

هندسة تكلفة الذكاء الاصطناعي وتوجيه النماذج

AI Engineering Track · 3 teaching days + capstone day · 21 hours · Level 300

Make the cost of language model applications measurable, attributable and smaller, without losing quality

Participants make the cost of language model applications measurable, attributable and smaller without losing quality. For a fictional telecom operator running three applications behind one gateway, a bilingual care assistant, a call-summary job and a billing-dispute agent, they work from a month of synthetic usage traces: they model cost per request and session, attribute spend to teams, set budgets, evaluate model tiers and reasoning settings on their own tasks, route with fallbacks, measure prefix and semantic caches, compare hosted and self-hosted serving and report cost per successful outcome. Cluster capacity planning is AE-307; engine-level optimisation is AE-401.

**Who it is for:** Practitioners. Engineers who have completed the level 200 set or can show equivalent work: a deployed model or language model application they built and can explain.

**Format:** Intensive: 3 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Mawj Telecom.** Mawj Telecom is a fictional regional mobile and fibre operator that runs three applications behind one model gateway, Maabar: Anis, a bilingual care assistant; Khulasa, a job that summarises calls; and Fasil, an agent that handles billing disputes. Participants work as its AI cost engineer on one month of synthetic gateway logs (about 97,000 rows), a provider invoice, a key register, price sheets, 100 labelled tasks per application and a data classification register, all generated with a fixed seed and holding no real personal data.

## The course

### Day 1: Where the money goes

Slides: https://sdaiaacademy.github.io/ae-312/slides/day1.md

- **Session 1: The token cost model**
  - Price one request from its token counts and a price sheet
  - Explain why cached, reasoning and failed tokens change the bill
  - Reconcile a cost model with an invoice line by line
  - [Lab 1.1: A cost model that matches the invoice (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D1_1_cost_model.ipynb)
- **Session 2: Agents, retries and long contexts**
  - Compute cost per session from request rows
  - Split a session into first attempts, retries, context growth and extra steps
  - Size the saving of a step budget and of a trimmed tool result
  - [Lab 1.2: The ten most expensive sessions (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D1_2_expensive_sessions.ipynb)
- **Session 3: Attribution and showback**
  - Attribute spend to team, application and environment through gateway keys and tags
  - Produce a showback table that adds up to the invoice, with an unallocated row
  - Compare two ways to allocate a cost that two teams share
  - [Lab 1.3: A showback table from gateway keys (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D1_3_showback.ipynb)
- **Session 4: Budgets and limits**
  - Write soft and hard budgets per application and environment
  - Replay a spike and read which requests the gateway refused
  - Choose between a budget and a rate limit for a given failure
  - [Lab 1.4: Soft and hard budgets, and a spike (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D1_4_budgets.ipynb)

### Day 2: Route and cache

Slides: https://sdaiaacademy.github.io/ae-312/slides/day2.md

- **Session 1: Own tasks, several settings**
  - Write a code grader for the care assistant and score six configurations
  - Report quality, latency and cost per task, split by language
  - Check supplied results against a live rerun of ten tasks
  - [Lab 2.1: Three tiers, two reasoning settings, your own tasks (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D2_1_own_tasks.ipynb)
- **Session 2: Routing and cascades**
  - Build a cascade with a quality check that needs no label and a fallback on errors
  - Measure cost per successful outcome, failed first attempts included
  - Write a router configuration that keeps the floor in Arabic and English
  - [Lab 2.2: A two-tier router with a quality check (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D2_2_router.ipynb)
- **Session 3: Prompt layout for prefix caching**
  - Explain how a prefix cache matches and how long it keeps an entry
  - Find what breaks the shared prefix of two prompts
  - Measure hit rate, cost and time to first token before and after a new layout
  - [Lab 2.3: Prompt layout for prefix reuse (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D2_3_prefix_cache.ipynb)
- **Session 4: Semantic caches and their risks**
  - Measure hit rate and wrong-answer rate of a semantic cache at several thresholds
  - Scope cache entries so that no answer crosses customers
  - Write the isolation test that proves it
  - [Lab 2.4: A semantic cache and its wrong answers (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D2_4_semantic_cache.ipynb)

### Day 3: Host or buy, and report

Slides: https://sdaiaacademy.github.io/ae-312/slides/day3.md

- **Session 1: Self-hosting economics**
  - Compute cost per request of a self-hosted model as a function of utilisation
  - Find break-even utilisation against API prices and draw it
  - Apply the classification register before comparing prices
  - [Lab 3.1: Break-even utilisation for self-hosting (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D3_1_break_even.ipynb)
- **Session 2: Batch versus interactive**
  - Recompute the cost of a job on a batch tier
  - Estimate turnaround under a submission schedule from completion times
  - Split a workload into what can wait and what cannot
  - [Lab 3.2: The call-summary job on a batch tier (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D3_2_batch_tier.ipynb)
- **Session 3: Cost per successful outcome**
  - Join session cost with evaluation outcomes and report what did not join
  - Compute cost per request, per session and per resolved dispute
  - Compare two configurations at a quality floor, human escalations included
  - [Lab 3.3: Cost per resolved dispute (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D3_3_cost_per_outcome.ipynb)
- **Session 4: The cost review**
  - Rank savings options by measured saving, quality effect and risk
  - Report energy per thousand requests beside cost
  - Draft a two-page cost review and choose the capstone scenario
  - [Lab 3.4: The two-page cost review (25 min)](https://sdaiaacademy.github.io/ae-312/labs/D3_4_cost_review.ipynb)

### Capstone: Capstone: the cost review, defended

Slides: https://sdaiaacademy.github.io/ae-312/slides/capstone.md

## Capstone

A cost review of an unseen scenario: a public repository with the notebook, measured routing and caching results and a two-page memo with three savings options, defended in ten minutes

**What you submit:** A public GitHub repository link: the notebook with its execution log, the gateway log of the replayed spike, the router file, the cache measurements and the isolation test, and the two-page review (three savings options, each with its measured saving, its effect on quality in Arabic and English, its risk, and energy per thousand requests beside cost). Then a ten-minute live defence: the participant recomputes one savings figure the assessor picks and explains one routing decision.

**Rubric:**

- Cost model accuracy: 20%
- Routing evaluation: 25%
- Caching evidence: 20%
- Hosting analysis: 20%
- Review quality: 15%

## Outcomes

- **LO1** Compute cost per request and per session from prompt, output and cached tokens, retries, agent steps and accelerator-hours, given a month of usage traces and a synthetic invoice (Applied) Evidence: a cost model that reconciles with the invoice within 2%
- **LO2** Configure attribution, budgets and limits per team, application and environment on a model gateway, given three applications sharing one gateway (Applied) Evidence: a showback table and a replayed spike that trips the hard limit
- **LO3** Evaluate model tiers, reasoning settings and a routing policy on the operator's own tasks, choosing by cost per successful outcome at a fixed quality floor, given 100 labelled tasks per application (Performance) Evidence: a results table and a router configuration with its measured savings
- **LO4** Measure how prefix and semantic caching change cost, latency and answer correctness, including isolation between customers, given replayed traffic for the care assistant (Applied) Evidence: hit rates, a wrong-answer rate and a passing cross-customer isolation test
- **LO5** Decide between hosted APIs and a self-hosted open-weight model with a break-even analysis that includes utilisation and data-placement rules, given price sheets, a throughput benchmark and the operator's classification register (Performance) Evidence: a break-even chart and a recommendation
- **LO6** Deliver a cost review with three measured savings options to engineering and finance stakeholders, given an unseen capstone scenario (Performance) Evidence: a notebook and a two-page review reporting energy beside cost, defended in ten minutes

## Tools

- **Model gateway with budgets and routing:** LiteLLM, Agent Router
- **Language model access:** a locally served open-weight model, a free hosted open-weight model, any commercial API
- **Evaluation harness:** promptfoo, Inspect
- **Usage analysis:** DuckDB, pandas
- **Cache stores:** Valkey, PostgreSQL with pgvector
- **Local inference server:** vLLM, llama.cpp

## Prerequisites

- AE-203 Building Applications on Language Models
- AE-205 Deploying AI Services: Containers, Serving and Monitoring
- Groups and joins usage logs with SQL or dataframes
- Has run an evaluation set against a language model application
- Setup: a laptop CPU with uv, or Google Colab. Eleven of the twelve labs call no model; one step of Lab 2.1 calls a free hosted model and falls back to supplied outputs without a key. Nothing downloads a model. See labs/README.md.

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

---

SDAIA Academy · AI Engineering Track · AI Cost Engineering and Model Routing

Course version 2027.1.0 · engine 1.0.0 · built 2026-11-15 · commit 2f622db
