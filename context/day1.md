---
course: "AI Cost Engineering and Model Routing"
code: "AE-312"
version: "2027.2.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-312/slides/day1.html"
---

# AI Cost Engineering and Model Routing

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
