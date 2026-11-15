---
course: "AI Cost Engineering and Model Routing"
code: "AE-312"
version: "2027.1.0"
scope: "course"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-312/"
---

# AI Cost Engineering and Model Routing

Make the cost of language model applications measurable, attributable and smaller, without losing quality

Participants make the cost of language model applications measurable, attributable and smaller without losing quality. For a fictional telecom operator running three applications behind one gateway, a bilingual care assistant, a call-summary job and a billing-dispute agent, they work from a month of synthetic usage traces: they model cost per request and session, attribute spend to teams, set budgets, evaluate model tiers and reasoning settings on their own tasks, route with fallbacks, measure prefix and semantic caches, compare hosted and self-hosted serving and report cost per successful outcome. Cluster capacity planning is AE-307; engine-level optimisation is AE-401.

- **Audience:** Practitioners. Engineers who have completed the level 200 set or can show equivalent work: a deployed model or language model application they built and can explain.
- **Prerequisites:** AE-203 Building Applications on Language Models; AE-205 Deploying AI Services: Containers, Serving and Monitoring; Groups and joins usage logs with SQL or dataframes; Has run an evaluation set against a language model application; Setup: a laptop CPU with uv, or Google Colab. Eleven of the twelve labs call no model; one step of Lab 2.1 calls a free hosted model and falls back to supplied outputs without a key. Nothing downloads a model. See labs/README.md.
- **Case study:** Mawj Telecom: Mawj Telecom is a fictional regional mobile and fibre operator that runs three applications behind one model gateway, Maabar: Anis, a bilingual care assistant; Khulasa, a job that summarises calls; and Fasil, an agent that handles billing disputes. Participants work as its AI cost engineer on one month of synthetic gateway logs (about 97,000 rows), a provider invoice, a key register, price sheets, 100 labelled tasks per application and a data classification register, all generated with a fixed seed and holding no real personal data.

## Outcomes

- LO1 (Applied): Compute cost per request and per session from prompt, output and cached tokens, retries, agent steps and accelerator-hours, given a month of usage traces and a synthetic invoice
- LO2 (Applied): Configure attribution, budgets and limits per team, application and environment on a model gateway, given three applications sharing one gateway
- LO3 (Performance): Evaluate model tiers, reasoning settings and a routing policy on the operator's own tasks, choosing by cost per successful outcome at a fixed quality floor, given 100 labelled tasks per application
- LO4 (Applied): Measure how prefix and semantic caching change cost, latency and answer correctness, including isolation between customers, given replayed traffic for the care assistant
- LO5 (Performance): Decide between hosted APIs and a self-hosted open-weight model with a break-even analysis that includes utilisation and data-placement rules, given price sheets, a throughput benchmark and the operator's classification register
- LO6 (Performance): Deliver a cost review with three measured savings options to engineering and finance stakeholders, given an unseen capstone scenario

## Day 1: Where the money goes

A cost model that matches the invoice, the sessions that cost the most, who spent what, and budgets that hold

#### [day1#title] Where the money goes

*SDAIA Academy · AI Cost Engineering and Model Routing*

Day 1: A cost model that matches the invoice, the sessions that cost the most, who spent what, and budgets that hold

AI Engineering Track · 3 teaching days + capstone day · 4 sessions · 4 labs · AE-312

#### [day1#agenda] Where the money goes

*Today*

- **Session 1 · The token cost model**: What a request costs: uncached, cached, output and reasoning tokens, and what the provider bills when a call fails
- **Session 2 · Agents, retries and long contexts**: Why an agent session costs far more than its number of steps suggests, and where retries and long contexts hide
- **Session 3 · Attribution and showback**: From one invoice to who spent what: keys, tags, a showback table and the costs nobody owns
- **Session 4 · Budgets and limits**: Budgets that warn and budgets that refuse, and why their scope decides who is refused

### Session 1: The token cost model

#### [day1#s1] The token cost model

*Session 1*

- Price one request from its token counts and a price sheet
- Explain why cached, reasoning and failed tokens change the bill
- Reconcile a cost model with an invoice line by line

#### [day1#mawj-three-applications] Mawj Telecom runs three applications behind one gateway

*The case study*

- **Anis.** A bilingual care assistant. 37,974 requests in October, SAR 911.
- **Khulasa.** A job that summarises calls. 25,633 tagged requests, SAR 846, and a pilot on a leased node.
- **Fasil.** An agent that handles billing disputes. 3,200 sessions, SAR 2,515.

All three call the provider through **Maabar**, the gateway, which logs one row per attempt: 97,318 rows for the month. The invoice says SAR 8,242.62. You are the cost engineer who has to explain it.

#### [day1#price-sheet] A request costs its tokens times the price of each kind

*Recap from AE-203*

| Tier | Input | Cached input | Output |
| --- | --- | --- | --- |
| `tier-s` | 0.60 | 0.06 | 2.40 |
| `tier-m` | 3.00 | 0.30 | 12.00 |
| `tier-l` | 12.00 | 1.20 | 48.00 |

SAR per million tokens. A synthetic price sheet for the labs, not a provider's.

> **The shape is what lasts.** Output costs several times input, cached input a fraction of input, and each tier several times the one below. The figures change every few months.

#### [day1#prefill-and-decode] Reading a prompt and writing an answer are different work

*Why the prices differ*

- **Prefill.** The model reads the whole prompt in one pass. Cheap per token, and paid again on every call.
- **Decode.** The model writes one token at a time, each needing a pass. Expensive per token, and it sets the latency.
- **Cached prefix.** A prompt start the provider has already read is not read again. Billed at a fraction of the input price.

One answer of Anis: 6,831 tokens in, 199 out, SAR 0.0229. The input side is **90%** of it, because every turn resends the instructions and the policy text.

#### [day1#four-kinds-of-token] A log row holds four kinds of token, and they overlap

*The cost model*

```python
# file: the cost of one row, in SAR
uncached = input_tokens - cached_tokens        # input INCLUDES cached
cost = ( uncached          * price["input"]
       + cached_tokens     * price["cached_input"]
       + (output_tokens + reasoning_tokens) * price["output"]   # output EXCLUDES reasoning
       ) / 1e6
```

> **What goes wrong.** Each provider and each gateway defines these fields its own way. Read the definition before you sum a column: whether input includes cached tokens, and whether output includes reasoning tokens.

#### [day1#what-a-failure-costs] A failed call can still be a billed call

*Retries*

| Status in the log | What happened | Billed? |
| --- | --- | --- |
| `ok` | The answer arrived | Yes |
| `timeout` | The client gave up; the provider had started to answer | Yes: the prompt and what was written so far |
| `error` | The provider refused the request | No |

October has 1,751 timeouts in the log. They cost SAR 57 and nobody received their answers.

#### [day1#close-for-the-wrong-reasons] The naive model is 2% off, for two large reasons that cancel

*Lab 1.1 · the result*

| Cost model | SAR | Against the invoice |
| --- | --- | --- |
| Naive: successful rows, input and output | 4,870.75 | +2.1% |
| + cached input at the cached price | 3,076.23 | -35.5% |
| + reasoning tokens as output | 4,651.17 | -2.5% |
| + billed timeouts | 4,708.59 | -1.3% |

> **Close is not correct.** A model that lands near the invoice because two errors cancel breaks in the month the traffic mix changes.

#### [day1#accelerator-hours] A leased accelerator is paid by the hour, used or idle

*The other unit of cost*

- Khulasa's pilot leased one node for 8 hours a night: **248 hours at SAR 14**, SAR 3,472 on the invoice.
- It served 4,500 summaries and was busy **18%** of its leased time.
- Cost per request is the lease over the requests served. Tokens on the node have no price.

- **0.772** SAR per summary on the node
- **0.033** SAR for the same job on the API

#### [day1#reconcile-by-line] Reconcile by invoice line, and give the gap a name

*The evidence for this outcome*

1. **1 · Quantities** tokens by model and kind, from the log
2. **2 · Lines** beside each invoice line
3. **3 · Gap** what has no row of yours

Every line billed to the gateway's key matches the log token for token. The cost model gives SAR 8,180.59 against SAR 8,242.62: a gap of **0.75%**, all of it on a provider key the gateway never issued.

#### [day1#check-cost-model] A model that is 1% under

*Checkpoint*

**Question:** A colleague's cost model sums the successful rows of the log and lands 1% under the invoice in a calm month. The next month has a two-hour provider incident. What happens to the gap?

- A. It stays near 1%, because failed calls are not billed
- B. It shrinks, because fewer requests succeed
- C. It widens, because timeouts are billed and the model leaves them out
- D. It moves at random from month to month

#### [day1#lab-1-1] A cost model that matches the invoice

Lab 1.1 · 25 min

Compute cost per request for the three applications and reconcile it with the synthetic invoice: from a naive model that is close for the wrong reasons to one that matches line by line, within 2% in total.

[D1_1_cost_model.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D1_1_cost_model.ipynb)

- [ ] Price one request by hand from the price sheet (5 min)
- [ ] The month with a naive model, against the invoice (5 min)
- [ ] Add cached tokens, reasoning tokens and billed failures (7 min)
- [ ] Add the accelerator-hours of the pilot node (4 min)
- [ ] Reconcile line by line and state the gap (4 min)
- [ ] ✱ Stretch: Find the spend the gateway never saw

### Session 2: Agents, retries and long contexts

#### [day1#s2] Agents, retries and long contexts

*Session 2*

- Compute cost per session from request rows
- Split a session into first attempts, retries, context growth and extra steps
- Size the saving of a step budget and of a trimmed tool result

#### [day1#session-is-the-unit] An agent's bill is counted in sessions, not in requests

*The unit of work*

- **0.72** SAR, the median session of the dispute agent
- **11.07** SAR, its most expensive session
- **15x** the median, in one session of 70 steps

The ten most expensive sessions of October all belong to the dispute agent. An average cost per request hides every one of them.

#### [day1#every-step-resends] Every step resends everything before it

*Context growth*

- step 1: 3,980 tokens in, none cached
- step 2: 6,377 tokens in, 3,968 of them cached
- step 8: 9,441 tokens in, 9,088 cached
- step 70: 34,823 tokens in, 34,304 cached, after one billed timeout

> **Cost grows faster than steps.** Twice the steps is more than twice the cost, since each step's prompt holds all the earlier ones. In this session half of the cost came after step 44.

#### [day1#cache-carries-the-agent] An agent loop is affordable because its prefix is cached

*Cached tokens, again*

| Item | Value |
| --- | --- |
| The agent's month, as billed | SAR 2,515 |
| The same month with no cached token | SAR 4,339 |

- Each step's prompt starts with the previous step's prompt, so most of it is billed at the cached price.
- Anything that breaks that prefix, such as a new model or an edited history, is paid at the full input price.

#### [day1#retries-multiply] A retry resends the whole prompt, and an incident multiplies retries

*Retries*

- The worst session made **95 attempts for 70 steps**; 24 of them were billed timeouts.
- A client that retries at once, up to four times, turns one provider incident into several times the load.
- Retries are small in SAR here, 1.5% of the agent's month, and large in waiting: each timeout is a customer who waited a minute.

- **What to configure.** Fewer attempts, a growing pause between them, and a circuit breaker that stops calling a provider that keeps failing.

#### [day1#four-parts-of-a-session] Split a session's bill into four parts

*Lab 1.2 · the split*

| Part | What it is | October, SAR | Share |
| --- | --- | --- | --- |
| Base | the steps within a budget of 12, at the first step's prompt size | 1,889.66 | 75.1% |
| Context growth | input beyond the first step's prompt | 455.25 | 18.1% |
| Extra steps | steps beyond the budget | 131.78 | 5.2% |
| Retries | billed attempts that did not succeed | 38.40 | 1.5% |

#### [day1#tool-that-returns-a-year] One tool without paging fills the context for the rest of the session

*Long contexts*

- In 124 of 3,200 sessions a tool returned a year of itemised bills, and returned it again on later calls.
- Those 4% of sessions hold SAR 188 of the SAR 455 of context growth.
- One of them reached a prompt of 436,891 tokens in 8 steps and cost SAR 7.42.

- **The fix is in the tool.** Return the three bills the dispute names, with a way to ask for more. A result the model does not need is paid for at every later step.

#### [day1#three-fixes-sized] Three causes, three fixes, each with its size

*Measure before optimising*

| Cause | Fix | At stake in October |
| --- | --- | --- |
| The agent loops | a step budget and a stop rule for "pending" | SAR 131.78 |
| A tool returns too much | page and trim tool results | up to SAR 188.47 |
| Timeouts retried at once | fewer attempts, a pause, a circuit breaker | SAR 38.40 |

> **Size first.** The fix that sounds most urgent after an incident is not always the largest. A table like this is what a cost review is made of.

#### [day1#check-agent-cost] Twice the steps

*Checkpoint*

**Question:** After a change to a tool, the dispute agent takes 12 steps per session where it took 6. Nothing else changed and the prefix cache still works. What happens to the cost of a session?

- A. It more than doubles, because each added step also resends a longer history
- B. It doubles, because cost is proportional to steps
- C. It barely moves, because the history is cached
- D. It stays the same, because only failed steps add cost

#### [day1#lab-1-2] The ten most expensive sessions

Lab 1.2 · 25 min

Find the ten most expensive sessions and attribute their cost to steps, retries and context growth, then size a fix for each cause.

[D1_2_expensive_sessions.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D1_2_expensive_sessions.ipynb)

- [ ] Cost per session, and the top ten (5 min)
- [ ] Split each session: base, context growth, extra steps, retries (9 min)
- [ ] Read the worst session step by step (5 min)
- [ ] Three causes, three fixes and their size (6 min)
- [ ] ✱ Stretch: What the agent would cost without its prefix cache

### Session 3: Attribution and showback

#### [day1#s3] Attribution and showback

*Session 3*

- Attribute spend to team, application and environment through gateway keys and tags
- Produce a showback table that adds up to the invoice, with an unallocated row
- Compare two ways to allocate a cost that two teams share

#### [day1#allocate-first] Allocate first, then optimise

*Attribution*

- One invoice, five teams: until spend has an owner, nobody has a reason to lower it.
- An owner is a **team**, an **application** and an **environment**.
- The gateway is where that is recorded, because every request passes through it.

- **At Mawj.** Shurooq in finance receives one PDF a month. The question she is asked is always "whose is it?", and the invoice has no column for that.

#### [day1#keys-and-tags] A key says who is calling; a tag says what for

*Two mechanisms*

- **A gateway key.** Issued to one team, for one application, in one environment. Attribution costs nothing: it is the join of the log with the key register.
- **A tag on the request.** Sent by the application: `app=khulasa;caller=fasil`. Finer than a key, and only as reliable as the code that sets it.

> **Prefer keys.** A key cannot be forgotten: a request without one is refused. A tag can be left out, and in October it was on 8% of the shared key's requests.

#### [day1#shared-key] The register says one team spent SAR 1,157. Three things are inside

*Lab 1.3 · what the register hides*

| On `key-shared-legacy` | Requests | SAR |
| --- | --- | --- |
| Khulasa, tagged | 25,633 | 846.21 |
| Another team's experiment on the large tier | 1,115 | 239.90 |
| No tag at all | 2,161 | 70.48 |

> **What goes wrong.** A key issued "for now" before keys per application existed. A team without a key borrowed it for a week, at SAR 0.215 a request against Khulasa's SAR 0.033.

#### [day1#unallocated-is-a-row] What nobody owns gets its own row

*Honest tables*

- **Untagged requests** on the shared key: SAR 70.48.
- **A provider key outside the gateway**: SAR 62.02, on the invoice and in no log.
- Together **1.6%** of the invoice: small, visible, and somebody's job to shrink.

- **Do not spread it.** Giving unallocated spend to the largest team, or to everyone by share, makes the table add up and removes the reason to fix the tags.

#### [day1#showback-table] The showback table adds up to the invoice

*Lab 1.3 · the result*

| Item | Value |
| --- | --- |
| Contact-centre analytics | SAR 4,318 · 52.4% |
| Billing operations | SAR 2,581 · 31.3% |
| Customer care | SAR 971 · 11.8% |
| Network analytics | SAR 240 · 2.9% |
| Unallocated | SAR 133 · 1.6% |

Contact-centre analytics leads because of the node lease, SAR 3,472, not because of Khulasa's tokens.

#### [day1#showback-before-chargeback] Showback before chargeback

*A durable rule*

1. **1 · Showback** each team sees its spend; no money moves
2. **2 · Corrections** "that is not ours": tags and keys get fixed
3. **3 · Chargeback** budgets are charged, from a table people trust

> **Why the order.** The first tables are wrong in ways only the teams can see. A team charged from a table it never saw disputes the table, not its spend.

#### [day1#caller-or-owner] When one application calls another, there is no settled way to split the cost

*An open question*

- **Owner pays.** Khulasa's team pays for every summary, whoever asked. Simple; the owner carries other teams' demand.
- **Caller pays.** The dispute agent's team pays for the summaries it requests. Fairer on demand; the owner loses a reason to make the service cheaper.

At Mawj the rule moves **SAR 46.05** between two teams and changes nothing in the total. State the rule on the table; show what the other one would give.

#### [day1#check-untagged] The untagged 8%

*Checkpoint*

**Question:** 8% of the requests on a shared key carry no tag. Finance wants the showback table finished today. What do you do with their cost?

- A. Give it to the team that owns the key
- B. Spread it over all teams by their share of spend
- C. Leave it out, since it cannot be attributed
- D. Report it in an "unallocated" row and open the fix: a key per application

#### [day1#lab-1-3] A showback table from gateway keys

Lab 1.3 · 25 min

Tag spend by team, application and environment through gateway keys and produce a showback table that adds up to the invoice.

[D1_3_showback.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D1_3_showback.ipynb)

- [ ] Join the usage log to the key register (5 min)
- [ ] Split the shared key by its tags (6 min)
- [ ] Showback by team, application and environment (7 min)
- [ ] Calls between applications: caller pays or owner pays (7 min)
- [ ] ✱ Stretch: Spread the idle accelerator-hours by tokens and by requests

### Session 4: Budgets and limits

#### [day1#s4] Budgets and limits

*Session 4*

- Write soft and hard budgets per application and environment
- Replay a spike and read which requests the gateway refused
- Choose between a budget and a rate limit for a given failure

#### [day1#soft-and-hard] A soft budget tells someone; a hard budget refuses requests

*Budgets*

- **Soft level.** An alert when spend in the window crosses it. Nothing is refused.
- **Hard level.** Every later request in the scope is refused until the window ends.
- **Window and scope.** A day or a month; a key, an application, an environment, a team.

> **Use both.** Soft without hard is a message nobody must act on. Hard without soft is an outage with no warning.

#### [day1#scope-decides] One budget for the whole gateway refused the wrong application

*17 October, replayed*

- A tool outage made the dispute agent loop all afternoon.
- The gateway's single daily budget, SAR 260, was spent before the evening.
- Refused for the rest of the day: **474 requests of the care assistant**, 261 of the agent, 216 of Khulasa.
- 229 customers of Anis got no answer in its busiest hours.

- **The budget worked.** It stopped the spend. Its scope was the problem: the first application to overspend used up everyone's allowance.

#### [day1#levels-from-data] Levels come from the month's data, not from a round number

*Choosing the levels*

| Application | Median day | Highest normal day | Hard | Soft |
| --- | --- | --- | --- | --- |
| Anis | 32.9 | 36.0 | 60 | 48 |
| Khulasa | 28.3 | 32.1 | 70 | 56 |
| Fasil | 79.9 | 106.6 | 165 | 132 |

SAR per day, October without the incident day. Hard at about one and a half times the highest normal day; soft at 80% of hard.

#### [day1#policy-as-data] The policy is a file you can review, replay and version

*Lab 1.4 · the policy*

```json
// file: policy for Maabar (the lab's gateway model)
{"window": "day",
 "budgets": [
   {"scope": "app", "match": "anis",    "soft_sar": 48,  "hard_sar": 60},
   {"scope": "app", "match": "khulasa", "soft_sar": 56,  "hard_sar": 70},
   {"scope": "app", "match": "fasil",   "soft_sar": 132, "hard_sar": 165}],
 "rate_limits": [
   {"scope": "app", "match": "fasil", "requests_per_minute": 12}]}
```

#### [day1#hard-limit-trips] With budgets per application the hard limit trips on the agent only

*Lab 1.4 · the result*

- **39 min** from soft alert to hard limit
- **961** agent requests refused, in 28 sessions
- **0** requests of Anis refused
- **SAR 80** not spent that day

> **A refusal is not free.** Those 28 sessions were customers with a billing dispute. A hard limit needs a plan for them: hand the case to a person and say so.

#### [day1#rate-limit-or-budget] A rate limit acts in a minute; a budget acts in a day

*Limits*

- **Rate limit.** Requests or tokens per minute. For bursts and loops. At 12 requests a minute, twice the agent's busiest calm minute, the loop was slowed **2 hours 46 minutes** before the budget ran out.
- **Budget.** SAR per day or month. For the total. It does not notice a burst until the money is gone.

The cheapest control of all was not at the gateway: a step budget in the agent (Lab 1.2) ends a loop at step 12.

#### [day1#check-budget-scope] Three applications, one budget

*Checkpoint*

**Question:** A gateway has one hard daily budget for all applications. An internal batch job doubles its volume. At the end of the afternoon the budget is reached. Who is refused in the evening?

- A. Only the batch job, since it caused the overspend
- B. Every application in the scope, the customer-facing one included
- C. Nobody: the gateway sends an alert and keeps serving
- D. The applications with the lowest priority first

#### [day1#lab-1-4] Soft and hard budgets, and a spike

Lab 1.4 · 25 min

Set soft and hard budgets per application on the gateway and trip the hard limit with the replayed spike of day 17, without refusing the care assistant.

[D1_4_budgets.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D1_4_budgets.ipynb)

- [ ] Read the policy and replay a calm day (5 min)
- [ ] Replay the spike under one global budget (5 min)
- [ ] Budgets per application: soft and hard (8 min)
- [ ] Trip the hard limit and read the gateway log (4 min)
- [ ] A requests-per-minute limit for the agent (3 min)
- [ ] ✱ Stretch: A budget per environment, so that staging cannot spend production money

#### [day1#wrap-up] Where the money goes

*Day 1 · three things to keep*

- **Cost follows tokens, steps and utilisation.** Four kinds of token, billed failures, sessions that grow, and hours that are paid idle.
- **Measure before optimising.** Reconcile with the invoice, split the bill into parts, size each fix.
- **Allocate, then limit.** Keys per application, an unallocated row, showback first, budgets whose scope matches what they protect.

#### [day1#next] Route and cache

*Tomorrow*

Set the quality floor first, in Arabic and in English. Then find the cheapest configuration that keeps it, a router with a fallback, and two caches that are measured before they are trusted.

- Optional: a free key for a hosted model, for one step of Lab 2.1. Without it the step uses supplied outputs.
- Read the 100 tasks of one application in `labs/data/eval/`.

## Day 2: Route and cache

The cheapest configuration that keeps the quality floor, a router with a fallback, and two caches measured

#### [day2#title] Route and cache

*SDAIA Academy · AI Cost Engineering and Model Routing*

Day 2: The cheapest configuration that keeps the quality floor, a router with a fallback, and two caches measured

AI Engineering Track · 3 teaching days + capstone day · 4 sessions · 4 labs · AE-312

#### [day2#agenda] Route and cache

*Today*

- **Session 1 · Own tasks, several settings**: Choosing a tier and a reasoning setting on your own tasks, with a quality floor in each language
- **Session 2 · Routing and cascades**: Sending each request to the cheapest tier that can do it, and paying for the times it could not
- **Session 3 · Prompt layout for prefix caching**: A provider reuses a prompt only as far as it is identical from its first token: lay the prompt out for that
- **Session 4 · Semantic caches and their risks**: Answering a new question with an old answer: hit rates, wrong answers, stale answers and one customer seeing another's

#### [day2#review-day-1] Which request is on the bill?

*Review of Day 1*

**Question:** The dispute agent sends a prompt of 20,000 tokens, 19,200 of them cached. The client times out after the provider has written 300 tokens. How is this attempt billed?

- A. Not at all, because no answer arrived
- B. 800 input tokens at the input price, 19,200 at the cached price, 300 at the output price
- C. 20,000 tokens at the input price and 300 at the output price
- D. 20,000 at the input price, 19,200 more at the cached price, 300 at the output price

### Session 1: Own tasks, several settings

#### [day2#s1] Own tasks, several settings

*Session 1*

- Write a code grader for the care assistant and score six configurations
- Report quality, latency and cost per task, split by language
- Check supplied results against a live rerun of ten tasks

#### [day2#floor-first] Set the quality floor first, then cut cost

*The order of work*

1. **1 · Floor** the owner states the lowest acceptable pass rate
2. **2 · Measure** every candidate on your own tasks
3. **3 · Choose** the cheapest candidate above the floor

> **What goes wrong.** Prices are compared first, a cheap configuration is chosen, and the floor is then set wherever that configuration happens to land.

#### [day2#own-tasks] A leaderboard does not know your plans or your customers' Arabic

*Own-task evaluation*

- **100 labelled tasks per application**, half in English and half in Arabic, each with the facts a right answer must hold.
- **A grader in code**: the facts are there and the answer is in the customer's language.
- **Every candidate on the same tasks**: three tiers, two reasoning settings, with tokens and latency recorded.

- **One task of Anis.** كم سعر باقة Mawj 55 في الشهر وماذا تشمل؟
  Must include: 55, 10. Language: Arabic.

#### [day2#six-configurations] Six configurations on 100 tasks: quality, latency, cost

*Lab 2.1 · the care assistant*

| Tier | Reasoning | Pass rate | Median latency | SAR per task |
| --- | --- | --- | --- | --- |
| `tier-s` | off | 83% | 1.1 s | 0.0050 |
| `tier-s` | high | 85% | 3.6 s | 0.0065 |
| `tier-m` | off | 95% | 1.8 s | 0.0257 |
| `tier-m` | high | 96% | 6.7 s | 0.0333 |
| `tier-l` | off | 97% | 2.8 s | 0.1020 |
| `tier-l` | high | 98% | 10.6 s | 0.1347 |

#### [day2#floor-per-language] The small tier passes in English and fails in Arabic

*The floor holds in each language*

| Item | Value |
| --- | --- |
| tier-s · English | 92% |
| tier-s · Arabic | 74% |
| tier-m · English | 96% |
| tier-m · Arabic | 94% |

Floor: 92% in each language. An average of 83% says "a bit low"; the split says who pays for it. Six in ten of Anis's customers write in Arabic.

#### [day2#what-reasoning-buys] Reasoning is paid in output tokens and in seconds: buy it where it helps

*Reasoning settings*

- **Anis, a lookup.** High reasoning on the medium tier: 95% to 96%, one task. Cost up 30%, latency from 1.8 s to 6.7 s.
- **Fasil, a decision in several steps.** High reasoning on the medium tier: 76% to 91%. Without it, no tier reaches the floor of 90%.

> **A setting per application.** The reasoning setting is a second dial beside the tier, and the right position differs by task.

#### [day2#three-applications-three-answers] Three applications, three different answers

*The results table*

| Application | Runs on | Cheapest above the floor | Finding |
| --- | --- | --- | --- |
| Anis | tier-m, off | tier-m, off | right-sized as one tier; routing is the next step |
| Khulasa | tier-m, off | tier-s, off: 94%, SAR 0.0067 a task | 79% cheaper per task at the floor |
| Fasil | tier-l, high | tier-m, high: 91%, SAR 0.21 a task | passes the floor by one task: not settled |

#### [day2#one-task-is-two-points] With 50 tasks per language, one task is two points

*How much a table can say*

- 94% and 92% differ by **one task**. Do not rank on that.
- A configuration exactly on the floor has passed once, on this sample.
- More tasks, repeated runs, or a paired comparison narrow it. The size of the saving says how much care it deserves.

- **Report it this way.** "45 of 50 in Arabic, floor 46 of 50" is harder to misread than "90%".

#### [day2#check-the-recording] Supplied outputs are a recording: check a sample of it live

*Lab 2.1 · step 4*

1. **1 · Sample** ten tasks, five per language
2. **2 · Rerun** the same prompt against a live model
3. **3 · Compare** the same grader; read each disagreement

> **What it proves.** That the prompt, the task and the grader work on a real model. A free hosted model is not the provider's tier, so it does not confirm the pass rates.

#### [day2#check-floor-language] 95% overall

*Checkpoint*

**Question:** A cheaper configuration scores 95% on 100 tasks: 50 of 50 in English, 45 of 50 in Arabic. The floor is 92% in each language. Most customers write in Arabic. What do you report?

- A. It passes: 95% is above the floor
- B. It passes if the floor for Arabic is lowered to 90%
- C. It fails and should be dropped from the table
- D. It fails the floor in Arabic; it is a candidate for English traffic only

#### [day2#lab-2-1] Three tiers, two reasoning settings, your own tasks

Lab 2.1 · 25 min

Score supplied outputs of three model tiers at two reasoning settings on 100 tasks for quality, latency and cost, and rerun ten tasks live to check them.

[D2_1_own_tasks.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D2_1_own_tasks.ipynb)

- [ ] A grader for the care assistant (6 min)
- [ ] Score six configurations: quality, latency, cost (7 min)
- [ ] Split by language and apply the quality floor (5 min)
- [ ] Rerun ten tasks live and compare (7 min)
- [ ] ✱ Stretch: The same table for the call-summary job and the dispute agent

### Session 2: Routing and cascades

#### [day2#s2] Routing and cascades

*Session 2*

- Build a cascade with a quality check that needs no label and a fallback on errors
- Measure cost per successful outcome, failed first attempts included
- Write a router configuration that keeps the floor in Arabic and English

#### [day2#not-every-request] Most requests do not need the tier that the hardest ones need

*Routing*

- **5x** the price of tier-m over tier-s
- **46 of 50** English tasks of Anis the small tier answers right
- **37 of 50** Arabic tasks it answers right

One tier for everything pays the high price on every easy request. A router sends each request to the cheapest tier that can do it, and has to know which that is.

#### [day2#three-kinds-of-router] Three ways to decide where a request goes

*Tiers, cascades and learned routers*

- **A rule before the call.** By something known up front: language, application, intent. Costs nothing. As good as the measurement behind it.
- **A cascade.** Try the cheap tier, check the answer, escalate when the check fails. Pays twice for escalated requests.
- **A learned router.** A small model predicts whether the cheap tier will do. Needs training data and its own evaluation.

Lab 2.2 builds the first two. Whichever you use, it is judged the same way: cost per successful outcome at the floor.

#### [day2#check-without-label] In production nobody tells the router that an answer was wrong

*The quality check of a cascade*

- **What a check can see.** The call errored. The answer is empty. It is not in the language of the question. It hedges. It does not parse or breaks the schema.
- **What it cannot see.** A fluent answer, in the right language, with the wrong fee. Seeing that needs the right answer, or a grader as good as the large tier.

> **Measure the check too.** On labelled tasks, count the failures it catches, the failures it lets through and the right answers it rejects.

#### [day2#what-the-check-misses] The check catches the visible failures; in Arabic most are not visible

*Lab 2.2 · the check, measured*

| Failures of the small tier | English | Arabic |
| --- | --- | --- |
| Caught by the check, escalated | 2 | 5 |
| Let through: confident and wrong | 2 | 8 |
| Right answers rejected | 0 | 0 |

A plain cascade therefore ends at 48 of 50 in English and **42 of 50 in Arabic**: below the floor in the language of most customers.

#### [day2#cost-per-successful-outcome] Failed first attempts are paid: divide all spend by the successes

*The number to choose by*

```python
# file: cost per successful outcome
spend     = sum(cost of EVERY attempt, the rejected ones too)
successes = number of requests whose final answer was right
cost_per_successful_outcome = spend / successes
```

> **Two ways to fool yourself.** Counting only the final attempt's cost flatters a cascade. Dividing by requests instead of successes flatters a tier that is cheap and wrong.

#### [day2#router-results] The router that keeps both floors costs 38% less per success

*Lab 2.2 · the result*

| Policy | English | Arabic | SAR per success | Floor |
| --- | --- | --- | --- | --- |
| Always tier-s | 92% | 74% | 0.0060 | fails |
| Always tier-m | 96% | 94% | 0.0271 | holds |
| Cascade, s then m | 96% | 84% | 0.0075 | fails |
| Cascade for English, Arabic direct to m | 96% | 94% | 0.0167 | holds |

100 tasks of the care assistant, half in each language; supplied outputs.

#### [day2#fallback-is-not-escalation] A fallback answers an outage; an escalation answers a doubt

*Two reasons to call a second model*

- **Fallback.** The first model errored or timed out after its retries. The gateway calls another model. Protects availability.
- **Escalation.** The first model answered and the check rejected the answer. The router calls a stronger tier. Protects quality.

- A fallback target must have passed the same floor, or an outage quietly becomes a quality incident.
- Both are extra calls: both belong in cost per successful outcome.

#### [day2#switching-costs-cache] A cache belongs to one model: a switch in mid-conversation starts cold

*Cache cost of switching models*

- **0.0047** SAR, a turn on tier-m with a warm cache
- **0.0247** SAR, the same turn right after a switch

- The tier that takes over has never seen the prompt: 7,600 input tokens at the full price, **5.3 times** a warm turn.
- Route a conversation once, at its start, when you can.
- For an agent, a switch at step 20 repays the whole history.

#### [day2#check-cascade-cost] What the cascade costs

*Checkpoint*

**Question:** A cascade sends 100 requests to a tier at SAR 0.005 each. 20 fail the check and go to a tier at SAR 0.025. In the end 95 answers are right. What is the cost per successful outcome?

- A. SAR 0.0105: all 120 calls are paid, divided by 95 successes
- B. SAR 0.0100: total spend divided by 100 requests
- C. SAR 0.0095: 80 cheap calls and 20 dear ones, divided by 95
- D. SAR 0.0150: the mean of the two tiers' prices

#### [day2#lab-2-2] A two-tier router with a quality check

Lab 2.2 · 25 min

Build a two-tier router with a quality check and fallback and measure cost per successful outcome against always using one tier.

[D2_2_router.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D2_2_router.ipynb)

- [ ] Baselines: always small, always medium (4 min)
- [ ] A quality check that needs no label (6 min)
- [ ] The cascade, with fallback on errors (8 min)
- [ ] Cost per successful outcome, and the router file (7 min)
- [ ] ✱ Stretch: What a tier switch in the middle of a session costs in cache

### Session 3: Prompt layout for prefix caching

#### [day2#s3] Prompt layout for prefix caching

*Session 3*

- Explain how a prefix cache matches and how long it keeps an entry
- Find what breaks the shared prefix of two prompts
- Measure hit rate, cost and time to first token before and after a new layout

#### [day2#nothing-cached] Anis resends 8,400 tokens per request and none of them is cached

*The care assistant in October*

| Part of the prompt | Tokens |
| --- | --- |
| Clock | 14 |
| Customer profile | 27 |
| Instructions and plan sheet | 1,593 |
| Policy sections | 6,706 |
| History and question | 13 and up |

- 99% of the prompt is the same text for every customer.
- The provider caches prefixes and the log shows **0** cached tokens for Anis.
- The parts are in the order above.

#### [day2#how-a-prefix-cache-matches] A prompt is reused only as far as it is identical from its first token

*How a prefix cache works*

- **From the start.** The cache compares prompts from token 1. The first difference ends the match.
- **A minimum, in steps.** One large provider caches from 1,024 tokens and reports cached tokens in multiples of 128.
- **For minutes.** An unused entry expires after about 5 minutes with two large providers; a use refreshes it. Longer lifetimes exist, at a price.

> **Prices differ too.** With one large provider a cached read costs a tenth of the input price and writing a 5-minute entry costs 1.25 times it.

#### [day2#three-breakers] Three things break the shared prefix, and one is invisible in the template

*Lab 2.3 · the diagnosis*

| Layout | Two prompts are equal up to token | What differs there |
| --- | --- | --- |
| Today | 13 | a clock with seconds in the first line |
| Clock moved to the end | 2 | the customer's profile |
| Profile after the policies | 1,597 | the policy sections, in another order each time |
| Policy sections sorted | 8,301 | the two customers' profiles |

#### [day2#stable-first] Stable first, variable last

*Prompt layout*

1. **1 · Same for everyone** instructions, plan sheet, policy sections in a fixed order
2. **2 · Same in a conversation** profile, then history
3. **3 · New each request** the question, then the clock

> **History is a prefix too.** Turn 2 extends turn 1, so a conversation reuses its own earlier turns, if nothing that changes sits in front of them.

#### [day2#before-and-after] The same words in another order: 82% cheaper and first token sooner

*Lab 2.3 · the result*

- **0 → 98%** of input tokens read from the cache
- **60.19** SAR for two busy hours before
- **10.73** SAR after
- **-47%** median time to first token, 578 to 307 ms

2,219 replayed requests of two evening hours through the cache model. Every request hits once the cache is warm.

#### [day2#when-caching-loses] A cache pays when entries are reused before they expire

*The limits of the result*

| 45 requests, several minutes apart | Hit rate | SAR |
| --- | --- | --- |
| No cache | 0% | 1.214 |
| 5-minute entries, writes at 1.25 times input | 16% | 1.297 |
| One-hour entries, writes at 2 times input | 98% | 0.282 |

> **Do not multiply the peak by the month.** At night most entries expire between requests. With a write premium, a short-lived cache then costs more than no cache.

#### [day2#check-prefix] The template looks right

*Checkpoint*

**Question:** A prompt template puts 6,000 tokens of instructions and retrieved policy text first and the user's question last. Traffic is steady. The provider reports cached tokens on almost no request. What do you check first?

- A. Whether the cache lifetime is too short
- B. Whether the prompt is too short to be cached
- C. Whether two real prompts are identical token for token in that first part
- D. Whether a larger tier caches better

#### [day2#lab-2-3] Prompt layout for prefix reuse

Lab 2.3 · 25 min

Move stable content to the front of the care assistant's prompt and measure the cache hit rate and cost on two hours of replayed traffic.

[D2_3_prefix_cache.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D2_3_prefix_cache.ipynb)

- [ ] Replay the current layout through the prefix cache (5 min)
- [ ] Find what breaks the prefix (5 min)
- [ ] Reorder: stable first, variable last (8 min)
- [ ] Hit rate, cost and time to first token, before and after (7 min)
- [ ] ✱ Stretch: A quiet period: when does a cache with a write premium lose money?

### Session 4: Semantic caches and their risks

#### [day2#s4] Semantic caches and their risks

*Session 4*

- Measure hit rate and wrong-answer rate of a semantic cache at several thresholds
- Scope cache entries so that no answer crosses customers
- Write the isolation test that proves it

#### [day2#response-caches] A response cache skips the model: it serves an answer it gave before

*The other kind of cache*

- **Prefix cache.** At the provider. The model still answers; it reads less. Cannot return a wrong answer.
- **Exact response cache.** In your application. The same question, word for word, gets the stored answer.
- **Semantic response cache.** A question that is close enough to a stored one gets its answer. "Close enough" is a threshold on similarity.

> **A new kind of failure.** A response cache can serve an answer that was right for another question, another day or another customer.

#### [day2#hits-and-wrong-answers] A hit rate is half of a measurement

*Lab 2.4 · a cache with no scope*

| Cache | Hit rate | Wrong answers, of all questions | Another customer's answer |
| --- | --- | --- | --- |
| Exact match | 44.6% | 20.5% | 490 |
| Semantic, threshold 0.80 | 74.8% | 40.4% | 490 |
| Semantic, threshold 0.90 | 54.4% | 24.2% | 490 |
| Semantic, threshold 0.95 | 45.7% | 20.8% | 490 |

2,400 labelled questions to the care assistant over a month.

#### [day2#close-is-not-same] Two questions that differ in the one word that matters

*What a wrong hit looks like*

**Asked:** بعد الانتقال والهاتف الثابت في الطائف: لا توجد بيانات. ماذا أفعل؟

**Served from the cache (weak example):** The answer stored for: بعد الانتقال والهاتف الثابت في الطائف: رمز الخطأ 31. ماذا أفعل؟

Same device, same city, same wording; one says "no data", the other "error code 31". At threshold 0.80 they are close enough. Plans that differ by a number and "activate" against "deactivate" fail the same way.

#### [day2#isolation-is-not-a-threshold] No threshold stops one customer's answer reaching another

*Isolation between customers*

- "What is my current balance?" from two customers is the **same question**: similarity 1, and an exact match too.
- The answers differ because the **data** differs, not the words.
- 490 answers crossed at every threshold, and with the exact cache.

- **This is a disclosure.** A balance or a bill shown to the wrong person is personal data disclosed. It is an incident to report to the data protection officer, not a quality metric.

#### [day2#scope-the-entries] Scope every entry by whose data produced it, and test that nothing crosses

*Lab 2.4 · the fix and its test*

```python
# file: Lab 2.4
def scope_of(q):                      # known when the answer is written
    return f"customer:{q['customer']}" if q["used_customer_data"] else "public"

def test_no_answer_crosses_customers(served):
    assert served.crossed.sum() == 0
```

- An answer that read the customer's account lives in that customer's partition; everything else is shared.
- The test needs no labels. It fails on the unscoped cache and passes on the scoped one, at every threshold.

#### [day2#choose-the-threshold] With isolation fixed, the threshold trades hits for wrong answers

*Lab 2.4 · the scoped cache*

| Scoped cache, threshold | Hit rate | Wrong answers, of all questions | Crossed |
| --- | --- | --- | --- |
| 0.80 | 54.7% | 20.0% | 0 |
| 0.90 | 34.3% | 3.8% | 0 |
| 0.95 | 25.6% | 0.3% | 0 |

With at most 1% wrong answers allowed, 0.95 is the choice: a quarter of the questions served without the model, about SAR 233 of Anis's SAR 911 a month.

#### [day2#stale-answers] A cached answer is right until the world changes

*Staleness*

- On day 15 the price of one plan changed. At 0.95 the cache served the **old price twice**, on days 23 and 25.
- A 3-day lifetime on every entry removes both, and cuts the hit rate from 25.6% to **9.0%**.
- Better: tie entries to the version of what they were built from, and drop them when it changes.

- **Three questions for any cache.** Whose data is in the entry? How long is it true? What tells the cache that it no longer is?

#### [day2#check-semantic-cache] The balance of another customer

*Checkpoint*

**Question:** A semantic cache at threshold 0.90 served one customer the account balance of another. The team proposes to raise the threshold to 0.97. What do you answer?

- A. Agreed: at 0.97 only near-identical questions match
- B. It will not help: partition entries by customer when the answer used account data, and test it
- C. Use a stronger embedding model so the two questions separate
- D. Give the entries a lifetime of one hour

#### [day2#lab-2-4] A semantic cache and its wrong answers

Lab 2.4 · 25 min

Add a semantic cache to the care assistant, measure hit and wrong-answer rates at three thresholds and test that no answer crosses customers.

[D2_4_semantic_cache.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D2_4_semantic_cache.ipynb)

- [ ] An exact-match cache as the baseline (4 min)
- [ ] A semantic cache at three thresholds (7 min)
- [ ] The wrong-answer rate from labelled questions (6 min)
- [ ] An isolation test: failing, then passing (8 min)
- [ ] ✱ Stretch: A price changes on day 15: how long does the cache serve the old one?

#### [day2#wrap-up] Route and cache

*Day 2 · three things to keep*

- **The floor first, per language.** Own tasks, counts beside percentages, and no choice on a one-task difference.
- **Cost per successful outcome.** Every attempt is paid. A router is a result with a date and a traffic mix.
- **Measure a cache before trusting it.** Layout for the prefix cache; wrong answers, isolation and staleness for a response cache.

#### [day2#next] Host or buy, and report

*Tomorrow*

Where each dataset may be processed comes before any price. Then utilisation, a batch tier, the cost of a resolved dispute, and two pages for engineering and finance.

- Read `labs/data/hosting/classification_register.csv`: six rows.
- Think of one saving from today you would defend to a finance partner, and what you would say about its risk.

## Day 3: Host or buy, and report

Self-hosting against API prices after the data rules, a batch tier, cost per successful outcome and the review

#### [day3#title] Host or buy, and report

*SDAIA Academy · AI Cost Engineering and Model Routing*

Day 3: Self-hosting against API prices after the data rules, a batch tier, cost per successful outcome and the review

AI Engineering Track · 3 teaching days + capstone day · 4 sessions · 4 labs · AE-312

#### [day3#agenda] Host or buy, and report

*Today*

- **Session 1 · Self-hosting economics**: A leased accelerator costs the same used or idle: self-hosting is a question of utilisation, after the data rules
- **Session 2 · Batch versus interactive**: Work that can wait costs half: what waiting means for a job, and which requests cannot wait
- **Session 3 · Cost per successful outcome**: The unit that decides is the outcome the business wanted, with the failures and the people who clean up after them in the cost
- **Session 4 · The cost review**: Two pages for engineering and finance: three measured options, what each does to quality, risk and energy

#### [day3#review-day-2] A hit rate of zero

*Review of Day 2*

**Question:** An assistant sends 8,400 tokens per request, 8,000 of them identical for every customer. The provider reports no cached tokens. The prompt begins with the current time in seconds. What do you change first?

- A. Move the time to the end of the prompt, so the identical part comes first
- B. Add a semantic cache in front of the model
- C. Shorten the instructions to 6,000 tokens
- D. Ask the provider for a longer cache lifetime

### Session 1: Self-hosting economics

#### [day3#s1] Self-hosting economics

*Session 1*

- Compute cost per request of a self-hosted model as a function of utilisation
- Find break-even utilisation against API prices and draw it
- Apply the classification register before comparing prices

#### [day3#placement-before-price] Where a dataset may be processed comes before any price

*The first question*

| Dataset | Application | Classification | Placement rule | Transfer assessment |
| --- | --- | --- | --- | --- |
| Plan sheet and policy sections | Anis | Public | any region | not needed |
| Profile line and chat history | Anis | Restricted | in-Kingdom, or outside with an approved assessment | approved |
| Call transcripts | Khulasa | Restricted | in-Kingdom, or outside with an approved assessment | not approved |
| Itemised bills and payment records | Fasil | Restricted | in-Kingdom, or outside with an approved assessment | not approved |
| Dispute decisions and refunds | Fasil | Restricted | in-Kingdom only | not applicable |

Mawj's classification register, kept by Yaqoub Al-Nughaimshi, the data protection officer. Synthetic, like every file of the case.

#### [day3#what-the-register-rules-out] October's placement of two applications is not allowed

*Reading the register against the log*

- **Anis.** Global region or in-Kingdom: its transfer assessment was approved in September.
- **Khulasa.** In-Kingdom only. In October every transcript went to the global region.
- **Fasil.** In-Kingdom only. In October every bill went to the global region.

> **A cost review can raise a cost.** The in-Kingdom region is priced 30% above the global one on Mawj's sheet. Moving Fasil adds about SAR 755 a month, and it is not an option to decline.

#### [day3#a-node-bills-hours] A leased accelerator bills hours, used or idle

*Self-hosting*

- **14.00** SAR an hour, on demand
- **8.33** SAR an hour, reserved for the month (SAR 6,200)
- **3.36** SAR an hour of operations (SAR 2,500 a month of an engineer's time)

An API bills tokens: no traffic, no bill. A node bills time: the cost per request is the hourly cost divided by the requests served in that hour.

#### [day3#capacity-at-the-objective] Capacity is what the node serves while it still meets the latency objective

*The throughput benchmark*

| Concurrent requests | Requests a minute | 95th percentile latency |
| --- | --- | --- |
| 1 | 5.5 | 11.0 s |
| 4 | 20.0 | 12.5 s |
| 16 | 60.0 | 17.0 s |
| 32 | 84.0 | 26.0 s |
| 64 | 96.0 | 48.0 s |

Objective: 95% of summaries within 20 seconds. Capacity at the objective: **3,600 an hour**. A nightly job with no objective can take 5,760.

#### [day3#cost-against-utilisation] Cost per request falls with utilisation, and only with utilisation

*Lab 3.1 · step 2*

```python
# file: self-hosted cost per request, in SAR
served = capacity_per_hour * utilisation
cost_per_request = hourly_cost / served
# hourly_cost: the lease, plus operations
```

| Utilisation | SAR per summary |
| --- | --- |
| 1% | 0.3248 |
| 5% | 0.0650 |
| 18% | 0.0180 |
| 50% | 0.0065 |
| 90% | 0.0036 |

Reserved node with operations, SAR 11.69 an hour. The API price of the same summary: SAR 0.0434 on the medium tier and 0.0087 on the small tier, both in-Kingdom.

#### [day3#break-even] Break-even depends on which API price the node has to beat

*Lab 3.1 · step 3*

| Against | Break-even utilisation | Summaries a month needed | Times today's volume |
| --- | --- | --- | --- |
| Medium tier, global | 9.7% | 260,000 | 10.4 |
| Medium tier, in-Kingdom | 7.5% | 200,000 | 8.0 |
| Small tier, global | 48.6% | 1,302,000 | 51.9 |
| Small tier, in-Kingdom | 37.4% | 1,002,000 | 39.9 |

> **Compare with the right alternative.** Yesterday the small tier passed Khulasa's floor. The node has to beat that price, and it needs forty times today's volume to do it.

#### [day3#khulasa-four-options] Four options for Khulasa: placement, floor, then price

*Lab 3.1 · step 4*

| Option | SAR a month | Weaker language | Placement allowed |
| --- | --- | --- | --- |
| API, medium tier, global (October) | 838 | 96% | no |
| API, medium tier, in-Kingdom | 1,090 | 96% | yes |
| API, small tier, in-Kingdom | 218 | 92% | yes |
| Self-hosted, reserved node with operations | 8,700 | 94% | yes |

Floor: 92% in each language. The recommendation: the small tier in the in-Kingdom region, SAR 218 a month, with no margin in Arabic.

#### [day3#when-to-host-anyway] Three reasons to host that the chart does not show, and three costs

*Beyond the break-even*

- **Reasons.** A dataset no outside processor may see. A latency or availability need the provider does not meet. Steady volume near the node's capacity, day and night.
- **Costs.** The open-weight model has to pass the same floor, in both languages. Someone operates it. Every new model release reopens the comparison.

> **Write the conditions down.** "API today; revisit at 200,000 summaries a month or if the classification changes" is a recommendation. "Self-hosting is too expensive" is not.

#### [day3#check-break-even] A node at 15%

*Checkpoint*

**Question:** A team's leased node runs at 15% utilisation. Its break-even against the API tier the team uses today is 10%. A cheaper tier passed the quality floor last week; against it the break-even is 45%. What do you recommend?

- A. Keep the node: it is above its break-even
- B. Lease a second node to bring the cost per request down
- C. Move the work to the cheaper tier, and revisit the node if volume triples
- D. Reserve the node for a year to lower its hourly price

#### [day3#lab-3-1] Break-even utilisation for self-hosting

Lab 3.1 · 25 min

Fill a cost model for serving an open-weight model and find break-even utilisation against API prices, after the classification register has said where each dataset may go.

[D3_1_break_even.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D3_1_break_even.ipynb)

- [ ] Capacity at the latency objective, from the benchmark (5 min)
- [ ] Cost per request against utilisation (6 min)
- [ ] Break-even against the API prices, as a chart (7 min)
- [ ] The classification register first, then the recommendation (7 min)
- [ ] ✱ Stretch: Lease the node one hour a night: does the nightly job change the answer?

### Session 2: Batch versus interactive

#### [day3#s2] Batch versus interactive

*Session 2*

- Recompute the cost of a job on a batch tier
- Estimate turnaround under a submission schedule from completion times
- Split a workload into what can wait and what cannot

#### [day3#work-that-can-wait] Work that can wait costs half

*Batch tiers*

- You submit a file of requests; the provider answers them when it has spare capacity.
- The published terms of the large providers: **half the price**, results **within 24 hours**.
- No streaming and no conversation: each request stands alone and is matched to its answer by an identifier you set.

- **At Mawj.** Khulasa summarises a call after it has ended. Nobody is waiting on the line. It has run on the interactive tier since its first day.

#### [day3#the-month-on-batch] The same month on the batch tier: half, and the failed attempts disappear

*Lab 3.2 · steps 1 and 2*

- **1,132** SAR, 26,000 calls on the interactive tier, in-Kingdom
- **561** SAR, the same calls on the batch tier
- **546** failed interactive attempts that were billed: SAR 10

A batch has no client waiting, so no client times out and pays for an answer it never read.

#### [day3#within-24-hours] The promise is a ceiling; what you plan with is a distribution

*What "within 24 hours" means*

- **38 min** median completion of a batch
- **2 h 43** 95th percentile
- **6 h 49** the longest of the month

> **What goes wrong.** A team tests one batch, sees it finish in half an hour and promises that to the business. One batch in twenty takes more than five times as long.

#### [day3#turnaround] Turnaround is the wait for the next submission plus the completion time

*Lab 3.2 · step 3*

| Submission schedule | Median | 95th percentile | Within 12 hours |
| --- | --- | --- | --- |
| Every hour | 1.2 h | 3.0 h | 100% |
| Every 4 hours | 2.6 h | 4.6 h | 100% |
| Once a day | 11.1 h | 15.9 h | 58% |

Qutaiba Al-Ajaji's need: a summary in the customer's record within 12 hours of the call. The price is the same under all three schedules.

#### [day3#what-cannot-wait] Split the workload: 8% of the calls cannot wait

*Lab 3.2 · step 4*

1. **Urgent · 7.8%** complaints flagged for a call back: interactive tier, answer in seconds
2. **The rest · 92.2%** batch tier, submitted every 4 hours
3. **SAR 605 a month** 47% less than interactive, every summary on time

> **The headline discount is a ceiling.** What you save is the discount times the share of work that can wait.

#### [day3#stacking-discounts] Discounts stack only on the tokens they both touch

*Lab 3.2 · stretch*

- Batch halves every token. A cached prefix discounts the **stable part of the input** only.
- Khulasa's stable part is its instructions: about 1,000 tokens, **10% of an average prompt**. The transcript is the rest and never repeats.
- Batch plus cache: **7.8% more** off the batch price. Worth an afternoon, and it does not change the decision.

- **Compare with Anis.** Nearly all of Anis's prompt is stable, and the layout change saved 82%. The same technique, a different prompt, a different answer.

#### [day3#batch-in-operation] A batch job needs the same controls as an interactive one

*Before it ships*

- **Attribution.** The batch carries the tags of its application, or its spend lands in "unallocated" on the showback.
- **Budget.** One submitted file can hold a day's spend. The budget is checked before submission, not per request.
- **Partial results.** Some requests of a batch fail or expire. The job resubmits those, and counts them.

#### [day3#check-batch] A report by the morning

*Checkpoint*

**Question:** A job classifies 40,000 tickets a day. Its report is read the next morning, and 5% of the tickets are outage reports that an engineer must see within minutes. The batch tier costs half. What do you propose?

- A. Move every ticket to the batch tier, submitted once a day
- B. Keep every ticket on the interactive tier
- C. Move every ticket to the batch tier, submitted every five minutes
- D. Outage reports interactive, the rest in batches timed so the report is ready by the morning

#### [day3#lab-3-2] The call-summary job on a batch tier

Lab 3.2 · 25 min

Move the call-summary job to a batch tier and recompute cost and turnaround under three submission schedules, keeping urgent calls interactive.

[D3_2_batch_tier.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D3_2_batch_tier.ipynb)

- [ ] What the job costs on the interactive tier (4 min)
- [ ] The same month on the batch tier (5 min)
- [ ] Turnaround under three submission schedules (9 min)
- [ ] Keep the urgent calls interactive, and decide (7 min)
- [ ] ✱ Stretch: Stack the batch discount with a cached prefix

### Session 3: Cost per successful outcome

#### [day3#s3] Cost per successful outcome

*Session 3*

- Join session cost with evaluation outcomes and report what did not join
- Compute cost per request, per session and per resolved dispute
- Compare two configurations at a quality floor, human escalations included

#### [day3#three-denominators] The same money over three denominators gives three different stories

*The unit that decides*

- **0.11** SAR per request of the dispute agent
- **0.79** SAR per session
- **1.05** SAR per dispute resolved correctly

Humoud Al-Rubaian, who owns Fasil, does not buy requests. He needs disputes resolved, correctly. The unit of the review is the outcome the business wanted.

#### [day3#what-did-not-join] Cost and outcomes live in two systems, and the join never matches completely

*Lab 3.3 · step 1*

| Rows | Count |
| --- | --- |
| Sessions in the gateway log | 3,200 |
| Reviewed outcomes in the billing tool | 3,136 |
| Joined | 3,076 |
| Sessions without an outcome | 124 |
| Outcomes without a session | 60 |

- The 124 unreviewed sessions cost **SAR 85.82**. They were paid for.
- Cost in and outcome out makes the unit cost look worse; both out makes it look better.
- Choose one, say which, and report the other number beside it.

#### [day3#two-configurations] On the invoice, configuration B resolves a dispute for a third of the price

*Lab 3.3 · step 3*

| Configuration | Sessions | SAR per session | Resolved correctly | SAR per resolved dispute |
| --- | --- | --- | --- | --- |
| A · large tier, high reasoning | 733 | 0.917 | 81.4% | 1.125 |
| B · medium tier, high reasoning | 748 | 0.241 | 65.0% | 0.371 |

Same period for both: from the day B started, without the incident day. B has taken half of the sessions since then.

#### [day3#the-floor-in-production] B resolves fewer disputes, escalates twice as many and gets more of them wrong

*The quality floor, in production*

| Item | Value |
| --- | --- |
| A · escalated to a person | 11.3% |
| B · escalated to a person | 24.9% |
| A · wrong, of those it resolved | 5.1% |
| B · wrong, of those it resolved | 10.5% |

Humoud's floor for production: at most 6% of the disputes the agent resolves may be resolved wrongly. A holds it. B does not.

#### [day3#the-people-in-the-cost] With the people who handle its failures, the cheaper configuration costs twice as much

*Lab 3.3 · step 4*

| Per resolved dispute | A | B |
| --- | --- | --- |
| Model cost, SAR | 1.13 | 0.37 |
| With escalations and rework, SAR | 6.99 | 14.86 |
| The model's share of the total | 16% | 2% |

- **What a failure costs.** An escalated dispute is handled by a person: SAR 21. A wrong resolution comes back and is reworked: SAR 55. Figures from billing operations.

> **A review that stops at the invoice would have recommended B.** The saving moves to another team's budget, doubled.

#### [day3#choosing-the-outcome] Choose the outcome with the owner of the application, before you measure

*For your own applications*

| Application | A request is | The outcome is | Who records it |
| --- | --- | --- | --- |
| Anis | one answer | a conversation closed without a call to an agent | the contact centre |
| Khulasa | one summary | a summary an agent used without editing | the customer record tool |
| Fasil | one step | a dispute resolved correctly | the billing review |

> **No outcome recorded, no unit cost.** When nobody records the outcome, the first recommendation of the review is to start recording it.

#### [day3#check-cost-per-outcome] Half the price per session

*Checkpoint*

**Question:** A new configuration of an agent costs SAR 0.40 per session against 0.80 today. It completes 60% of sessions correctly against 80%, and each failed session is finished by a person at SAR 10. Which costs less per correctly completed task, people included?

- A. The new one: it costs half per session
- B. Today's: about SAR 3.50 against about SAR 7.30
- C. The new one: SAR 0.67 against 1.00 per success
- D. It cannot be said without the number of sessions

#### [day3#lab-3-3] Cost per resolved dispute

Lab 3.3 · 25 min

Join cost with evaluation outcomes and report cost per resolved dispute for two configurations of the dispute agent, with and without the cost of human escalations.

[D3_3_cost_per_outcome.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D3_3_cost_per_outcome.ipynb)

- [ ] Join session cost with outcomes, and count what did not join (6 min)
- [ ] Three unit costs: request, session, resolved dispute (6 min)
- [ ] Two configurations at the quality floor (7 min)
- [ ] Add the cost of human escalations (6 min)
- [ ] ✱ Stretch: An interval for the difference, by resampling sessions

### Session 4: The cost review

#### [day3#s4] The cost review

*Session 4*

- Rank savings options by measured saving, quality effect and risk
- Report energy per thousand requests beside cost
- Draft a two-page cost review and choose the capstone scenario

#### [day3#two-readers] Two pages, two readers, one decision

*The cost review*

- **Shurooq Al-Hamli, finance.** Reads the total, the three actions and their owners. Asks: is the saving real, and when does it show on the invoice?
- **Murtada Al-Awami, platform.** Reads how each figure was measured. Asks: on which traffic, at which floor, and what was not measured?

> **The review asks for a decision.** It names the actions, an owner for each, and what will be checked a month later.

#### [day3#seven-candidates] Seven candidates from three days, ranked by what they save

*Lab 3.4 · step 2*

| Candidate | SAR a month | % of the invoice | Holds its floor |
| --- | --- | --- | --- |
| Return the leased node | 3,472 | 42.1 | yes |
| Fasil: configuration B for every dispute | 2,162 | 26.2 | no |
| Anis: stable prompt layout | 749 | 9.1 | yes, to be retested |
| Khulasa: small tier, in-Kingdom | 620 | 7.5 | yes, at the floor in Arabic |
| Anis: router, Arabic direct to the medium tier | 350 | 4.2 | yes |
| Anis: scoped semantic cache | 233 | 2.8 | yes |
| Khulasa: batch every 4 hours | 102 | 1.2 | yes |

#### [day3#savings-do-not-add] Savings add across invoice lines, not on the same tokens

*Before you write a total*

- **These three add.** The node, Anis's layout and Khulasa's tier act on three different lines: SAR 4,841 a month together, 59% of October.
- **These do not.** The layout, the router and the semantic cache all act on Anis's input tokens. 82% and 38% are not 120%. Each acts on what the one before left.

> **What goes wrong.** A slide lists six savings measured separately and sums them. Finance books the sum, and the invoice never shows it.

#### [day3#energy-beside-cost] Report energy beside cost, and say where the figure comes from

*Energy per thousand requests*

| Application | SAR per 1,000 requests | Wh per 1,000 requests |
| --- | --- | --- |
| Anis | 24.48 | 327 |
| Khulasa | 33.72 | 467 |
| Fasil | 109.90 | 2,257 |

- The leased node drew about **451 kWh** in October for 4,500 summaries served: 100 Wh each, against under half a watt-hour on the hosted tier.
- The option that saves the most money saves the most energy, for the same reason: idle capacity.

> **Assumed, and labelled so.** The watt-hours per thousand tokens are assumptions in `data/hosting/energy.json`. They rank the options; they are not a measurement.

#### [day3#anatomy-of-the-review] Six short sections, in the order the readers ask their questions

*Lab 3.4 · step 3*

- **1 · What the month cost.** The invoice, how closely the model explains it, the showback by team, what could not be attributed.
- **2 · Three options.** Each with its saving, its quality in both languages and its risk.
- **3 · What we refuse.** The option someone will find on the invoice, and why it fails.
- **4 · Energy beside cost.** Before and after, per option, with the source of the figures.
- **5 · What was not measured.** In your own words. At least two things.
- **6 · The decision.** The total, a date, and for each action an owner and a check.

#### [day3#the-capstone] The capstone is another month at Mawj: nothing you measured carries over

*Lab 3.4 · step 4*

- **A · The care assistant doubles.** A campaign doubles Anis's traffic, and more spend bypasses the gateway.
- **B · The summary job triples.** Three times the calls, a larger pilot, a node leased twelve hours a night.
- **C · The dispute agent rolls out.** Twice the disputes, most of them on the cheaper configuration.

- **You submit** a public repository: the notebook, the measured results and the two-page review.
- **You defend it in ten minutes**: you recompute one savings figure the assessor picks and explain one routing decision.

#### [day3#check-review] The total on page one

*Checkpoint*

**Question:** A draft review lists a prompt layout change (82% off the assistant's spend), a router (38% off) and a semantic cache (25% off), each measured alone on the same assistant, and promises finance the three together. What do you change?

- A. Measure the three applied together in shipping order, or promise only the first
- B. Nothing: the three percentages add up to the total saving
- C. Report the average of the three, 48%
- D. Keep the largest and delete the other two from the review

#### [day3#lab-3-4] The two-page cost review

Lab 3.4 · 25 min

Draft a two-page review with three measured savings options from the numbers of the three days, then choose the capstone scenario and generate its data.

[D3_4_cost_review.ipynb](https://sdaiaacademy.github.io/ae-312/labs/D3_4_cost_review.ipynb)

- [ ] Collect the measured numbers of the three days (5 min)
- [ ] Three options: saving, quality effect, risk, energy (8 min)
- [ ] Write the two pages from the template (7 min)
- [ ] Choose the capstone scenario and generate its data (5 min)
- [ ] ✱ Stretch: Recompute one savings figure live, as in the defence

#### [day3#wrap-up] Host or buy, and report

*Day 3 · three things to keep*

- **Placement, floor, then price.** The register first. A node is a question of utilisation against the best allowed alternative.
- **The outcome is the unit.** Cost per resolved dispute, with the failures and the people who clean up after them.
- **Two pages that ask for a decision.** Three measured options, one refusal, energy beside cost, and what was not measured.

#### [day3#next] Your review, defended

*Capstone day*

An unseen month, a repository with measured results, two pages, and ten minutes in which you recompute one figure while the assessor watches.

- Generate your scenario and read `labs/capstone/README.md` before you start.
- Reconcile the cost model with the invoice first: no other number can be trusted before that.
- Rehearse the recomputation once, with a timer.

## Capstone: Capstone: the cost review, defended

An unseen scenario, a repository with measured results, a two-page review and a ten-minute live defence

#### [capstone#title] Capstone: the cost review, defended

*SDAIA Academy · AI Cost Engineering and Model Routing*

Capstone: An unseen scenario, a repository with measured results, a two-page review and a ten-minute live defence

AI Engineering Track · 3 teaching days + capstone day · 10 min talk and demo · AE-312

#### [capstone#agenda] How the presentations run

*Capstone*

- **Expectations and final prep**: the rubric, a last rehearsal, then the first presentations
- **Presentations**: ten minutes each, the assessor's questions included
- **Review and closing**: peer feedback, the trainer's review, what next

#### [capstone#rubric] The rubric

*How presentations are scored*

| Item | Value |
| --- | --- |
| Cost model accuracy | 20% |
| Routing evaluation | 25% |
| Caching evidence | 20% |
| Hosting analysis | 20% |
| Review quality | 15% |

> **Every figure in the review is printed by a cell of the notebook.** A saving without a measurement is a plan, not a result.

#### [capstone#format] 10 minutes for each defence

*Format*

- **1 · The month · 2 minutes.** Three numbers and the decision you ask for. Your review is on the screen.
- **2 · One figure, live · 5 minutes.** The assessor picks a savings figure. You recompute it from the log and say what it includes and what it leaves out.
- **3 · One routing decision · 3 minutes.** The assessor selects it. Which requests go where, what the check misses, what would change your mind.

> **No assistant during the defence.** Peer feedback after each one: a strength, a question and a suggestion.

#### [capstone#running-order] Who presents when

*Running order*

| # | Presenter | Scenario |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |
| 7 |  |  |
| 8 |  |  |

#### [capstone#final-prep] Final prep · 20 minutes

*Before the first presentation*

Run the notebook from the top once, rehearse one recomputation with a timer, open your review on this screen.

#### [capstone#now-presenting] Defence

*Now presenting*

#### [capstone#review] What the presentations showed

*Trainer review*

- **Strongest patterns.** What several projects got right.
- **Common gaps.** What most projects would fix next.
- **One surprise.** Something nobody expected.

#### [capstone#what-next] Keep going

*After the course*

- **Your review stays yours:** run it on one month of your own entity's usage log, with the outcome its owner names.
- **The follow-up task:** within a month, bring one saving that reached an invoice, with the quality figure beside it.
- **Next Academy courses:** AE-307 for cluster capacity planning, AE-401 for the serving engine and its optimisation.

#### [capstone#thanks] Thank you

*SDAIA Academy*

AI Cost Engineering and Model Routing
