---
course: "AI Cost Engineering and Model Routing"
code: "AE-312"
version: "2027.1.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-312/slides/day2.html"
---

# AI Cost Engineering and Model Routing

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
