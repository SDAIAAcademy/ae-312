# Answer key · for the trainer

Everything here comes from the solution runs on the committed data (`prepare_data.py`, seed 312, October 2026).
The same values are in `data/reference/`, one file per exercise. If you change the generator, run the solutions
again with `MAWJ_WRITE_REF=1` and update this file.

## Planted problems and the lab that finds each

| Planted in the data | Where | Found by |
|---|---|---|
| Input tokens include cached tokens; a naive model prices them all at the input price | `usage.csv.gz`, `prices.json` | Lab 1.1, step 2 |
| Reasoning tokens are billed as output and sit in their own column | `usage.csv.gz` | Lab 1.1, step 2 |
| 1,751 timed-out attempts were billed | `usage.csv.gz`, status `timeout` | Lab 1.1, step 2 |
| A provider key that bypasses the gateway: SAR 62.02 on the invoice, no rows in the log | `invoice.csv`, key `up-direct-7q2f` | Lab 1.1, step 4 |
| A leased node busy 18% of its hours: SAR 0.772 per summary against 0.033 on the API | `gpu_hours.csv` | Lab 1.1, step 3 |
| Agent loops on the incident day (17 October): sessions of 60 to 80 steps | `usage.csv.gz`, application `fasil` | Lab 1.2 |
| A tool that returns a year of bills: 124 long-context sessions | `usage.csv.gz`, application `fasil` | Lab 1.2, step 4 |
| A shared key with partly missing tags: SAR 70.48 cannot be attributed | `gateway/keys.csv`, `usage.csv.gz` | Lab 1.3 |
| One budget for the whole gateway: the loop makes the gateway refuse the care assistant | `gateway/policy_start.json` | Lab 1.4, step 1 |
| The small tier passes in English and fails in Arabic for Anis (92% and 74%) | `eval/outputs.jsonl.gz` | Lab 2.1 |
| Khulasa runs a tier above what its floor needs | `eval/outputs.jsonl.gz` | Lab 2.1, step 3 |
| The cascade's check misses more wrong answers in Arabic (8 of 13) than in English (2 of 4) | `eval/outputs.jsonl.gz` | Lab 2.2 |
| Three things break Anis's prefix: a clock in the first line, the profile before the instructions, policy sections in a varying order | `prompts/` | Lab 2.3, step 2 |
| Two customers ask for their balance in the same words: 490 answers cross at every threshold | `cache/anis_queries.jsonl` | Lab 2.4, step 2 |
| The price of a plan changes on day 15: a cache serves the old price on days 23 and 25 | `cache/anis_queries.jsonl` | Lab 2.4, stretch |
| Khulasa's and Fasil's data went to the global region; the register allows in-Kingdom only | `hosting/classification_register.csv` | Lab 3.1, step 4 |
| The pilot ran one request at a time: the node's capacity at the objective is 3,600 an hour | `hosting/throughput_benchmark.csv` | Lab 3.1, step 1 |
| 7.8% of calls are urgent and cannot wait for a batch | `hosting/khulasa_calls.csv` | Lab 3.2, step 4 |
| 124 sessions have no reviewed outcome and 60 outcomes have no production session | `outcomes/disputes.csv` | Lab 3.3, step 1 |
| Configuration B of Fasil is cheaper per resolved dispute and fails the floor on wrong resolutions | `outcomes/disputes.csv` | Lab 3.3, steps 3 and 4 |

## Expected numbers

**Lab 1.1.** Invoice SAR 8,242.62: tokens on the gateway's key 4,708.60, direct key 62.02, node 3,472.00 (248 hours at 14).
The naive model is 2.1% above the invoice, for the wrong reasons; with cached tokens priced 35.5% below; with reasoning
2.5% below; with billed timeouts 1.3% below; with the node the model totals SAR 8,180.59, a gap of 0.75%, which is the
direct key.

**Lab 1.2.** Median Fasil session SAR 0.715; the most expensive SAR 11.07 (70 steps, 95 attempts, 24 timeouts; half of
its cost is reached by step 44). The ten most expensive sessions are all Fasil's. The month in four parts: base
1,889.66, growth of the history 455.25, extra steps 131.78, retries 38.40. The 124 long-context sessions cost 188.47.
Caching carries the agent: without it the month would cost 4,339 against 2,515.

**Lab 1.3.** By team: contact-centre analytics 4,318.21 (52.4%), billing operations 2,580.74 (31.3%), customer care
971.22 (11.8%), network analytics 239.90 (2.9%), unallocated 132.50 (1.6%, of which 70.48 on the shared key and 62.02
on the direct key), platform 0.05. On the shared key: Khulasa 846.21, the network experiment 239.90. Caller-pays moves
SAR 46.05 between two teams.

**Lab 1.4.** One budget for the gateway (soft 208, hard 260) on the incident day: refused requests Anis 474, Fasil 261,
Khulasa 216; 229 customers of Anis refused. Budgets per application (Anis 48/60, Khulasa 56/70, Fasil 132/165): soft
to hard in 39 minutes, 961 requests refused in 28 sessions of Fasil only, SAR 79.88 not spent. With a limit of 12
requests a minute per session: 857 rate-limited, 349 refused by the budget.

**Lab 2.1.** Anis, pass rate (English, Arabic) and SAR per task: tier-s off 83% (92, 74) 0.0050; tier-m off 95% (96, 94)
0.0257; tier-l off 97% 0.1020. Chosen: tier-m, off. Khulasa: tier-s 94% (96, 92) at 0.0067 against tier-m at 0.0325,
79% cheaper. Fasil: tier-m with high reasoning 91% (92, 90) at 0.2058; tier-l with high reasoning 95% at 0.8201.
Step 4 on the stand-in agrees with the recording by construction.

**Lab 2.2.** Always tier-m: SAR 0.0271 per success. Cascade from tier-s: 90% (96, 84), below the floor in Arabic. Cascade
with Arabic sent directly to tier-m: 95% (96, 94) at 0.0167 per success, 38.4% less. The check catches 5 wrong answers
in Arabic and 2 in English, and misses 8 and 2. Switching tier in a conversation costs 5.3 times a cached turn.

**Lab 2.3.** Current layout: 0% of 2,219 requests reuse anything. Two prompts are equal up to token 13, then 2, then
1,597, then 8,301 as the three breakers are removed. Stable layout: 98.4% of input tokens read from the cache; the
two hours cost SAR 10.73 against 60.19 (82.2% less); median time to first token 307 ms against 578. Quiet period: no
cache 1.214, five minutes with writes at 1.25 times 1.297, one hour with writes at 2 times 0.282.

**Lab 2.4.** Unscoped cache: 490 answers cross between customers at every threshold. Scoped by customer where the
answer used account data: threshold 0.80 hit rate 54.7% with 20.0% wrong; 0.90 34.3% and 3.8%; 0.95 25.6% and 0.3%,
about SAR 233 a month. Chosen: scoped, 0.95. Stretch: two stale answers (days 23 and 25); a 3-day lifetime removes
them and cuts the hit rate to 9.0%.

**Lab 3.1.** Capacity 3,600 summaries an hour at a 95th percentile within 20 s, 5,760 without an objective. Hourly cost:
on demand 14.00, reserved 8.33, operations 3.36. Break-even utilisation of the reserved node with operations: 9.7%
against tier-m global, 7.5% against tier-m in-Kingdom, 48.6% against tier-s global, 37.4% against tier-s in-Kingdom
(40 times October's volume). Allowed regions: Anis both, Khulasa and Fasil in-Kingdom only. Options for Khulasa, SAR
a month: tier-m global 838.22 (not allowed), tier-m in-Kingdom 1,089.68, tier-s in-Kingdom 217.94 (recommended),
self-hosted 8,700. Stretch: one leased hour a night is SAR 434 for the node and 2,934 with operations. The
reservation pays above 442.9 leased hours a month (59.5% of the month): the pilot's 248 hours cost SAR 3,472 on demand
against 6,200 reserved, the nightly plan's 31 hours 434 against 6,200, and a node running all 744 hours 10,416 on
demand against 6,200, the only use to reserve.

**Lab 3.2.** 26,000 calls, 7.8% urgent, 546 failed attempts (SAR 10.19). Interactive SAR 1,131.82; all on the batch tier
560.82. Completion: median 38 minutes, 95th percentile 163, longest 409. Turnaround (median, 95th percentile, share
within 12 hours): every hour 1.2 h, 3.0 h, 100%; every 4 hours 2.6 h, 4.6 h, 100%; once a day 11.1 h, 15.9 h, 58%.
Decision: urgent calls interactive, the rest every 4 hours: SAR 604.57, 46.6% less. Stretch: a cached prefix takes
7.8% more off the batch price.

**Lab 3.3.** 3,200 sessions, 3,136 outcomes, 3,076 joined; 124 sessions without an outcome (SAR 85.82); 60 outcomes
without a session. Unit costs on the joined sessions: SAR 0.110 per request, 0.790 per session, 1.054 per correctly
resolved dispute. From day 16 without day 17: A 733 sessions, 0.917 per session, 81.4% resolved correctly, 11.3%
escalated, 5.1% of resolutions wrong, 1.125 per resolved dispute. B 748 sessions, 0.241, 65.0%, 24.9%, 10.5%, 0.371.
With people (escalation 21, rework 55): A 6.99, B 14.86. Stretch: B minus A is 7.91, middle 95% from 5.11 to 10.70.

**Lab 3.4.** Savings in SAR a month: the node 3,472.00; Fasil's configuration B 2,162.13 (fails its floor); Anis's layout
749.11; Khulasa on the small tier in-Kingdom 620.28; Anis's router 349.95; Anis's semantic cache 233.15; Khulasa's
batch plan 101.56. The three recommended: node, layout, Khulasa's tier: SAR 4,841.39 together. Per thousand requests:
Anis SAR 24.48 and 327 Wh, Khulasa 33.72 and 467 Wh, Fasil 109.90 and 2,257 Wh. The node: about 451 kWh in the month,
100 Wh per pilot summary served (4,500). Stretch: Khulasa recomputed with billed timeouts is 846.21 today and 220.01 on the small
tier in-Kingdom.

## What ran against a model

No step of the solution runs needed a model except Lab 2.1, step 4. In the author's run the hosted provider refused
the key (HTTP 401), so that step ran on the stand-in. Try it with a working key before the first cohort.
