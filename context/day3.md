---
course: "AI Cost Engineering and Model Routing"
code: "AE-312"
version: "2027.1.0"
deck: "day3"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-312/slides/day3.html"
---

# AI Cost Engineering and Model Routing

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
