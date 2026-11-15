# Capstone · The cost review, defended

The capstone is individual. You receive **another month at Mawj Telecom**: the same three applications on the same
gateway, with other volumes, another incident and another seed. Nothing you measured in the three teaching days
carries over. You publish a **public repository** with a notebook, its measured results and a **two-page cost
review** with three savings options. Then you defend it in a **ten-minute live defence**: you recompute one savings
figure the assessor picks, and you explain one routing decision the assessor selects.

All data is synthetic. Use no personal data and no internal document of your entity.

## The three scenarios

| | Scenario | What changed |
|---|---|---|
| **a** | The care assistant doubles | A campaign doubles the traffic of Anis for the month. A larger share of the spend bypasses the gateway, and the incident falls early in the month. |
| **b** | The call-summary job triples | Khulasa summarises three times as many calls, the pilot on the leased node has grown with it, and the node is leased twelve hours a night. Finance asks again whether Mawj should host the model itself. |
| **c** | The dispute agent rolls out | Fasil handles twice as many disputes, and the cheaper configuration has been taking most of them since the second week. Billing operations reports more reopened disputes. |

You choose one in Lab 3.4. The trainer may assign them so that the three are spread over the cohort.

## Getting started

```bash
# in your own repository, with the course's labs folder copied or cloned beside it
uv run python capstone/make_scenario.py b --out ../my-review/data
```

Point the course helpers at your scenario before you import them:

```python
import os
os.environ["MAWJ_DATA"] = "../my-review/data"   # the folder make_scenario.py wrote
import mawj as M                                  # M.usage(), M.invoice(), M.add_cost(...) now read your month
```

The scenario has **no reference state and no check cells**: `M.reference` has nothing to return. You write your own
checks. The helpers (`mawj.py`, `maabar.py`) and the price sheet are the same as in the labs.

## Minimum requirements

1. **A cost model that reconciles.** Cost per request and per session for the month, within 2% of the invoice,
   with every difference between a naive model and the invoice named.
2. **Attribution and limits.** A showback table by team, with what could not be attributed, and the incident day
   replayed through a budget policy of your own: the log of the replay is in the repository.
3. **Routing evaluation.** Tiers and one routing policy on the 100 tasks of at least one application, chosen by
   cost per successful outcome at the floor **in Arabic and in English**. The router is a file in the repository.
4. **Caching evidence.** Prefix reuse before and after a layout change, and a semantic cache with its wrong-answer
   rate and a **passing cross-customer isolation test**.
5. **Hosting analysis.** A break-even chart for the leased node at this month's volume, read **after** the
   classification register, with a recommendation and the conditions under which it would change.
6. **The two-page review.** Three savings options, each with its measured saving, its effect on quality in both
   languages, its risk, and energy per thousand requests beside cost. One option you do not recommend, with the
   reason. What you did not measure. Use `review/review_template.md` or your own layout.
7. **Reproducibility.** The notebook runs top to bottom from a clean clone, and its execution log is committed.
   Every number in the review is printed by a cell.

## Rubric

| Criterion | Points | Full marks look like |
|---|---|---|
| Cost model accuracy | 20 | Within 2% of the invoice; cached tokens, reasoning tokens, billed timeouts and the node each accounted for |
| Routing evaluation | 25 | A results table per language with counts, a router file, cost per successful outcome, and what the check misses |
| Caching evidence | 20 | Hit rates, cost and time to first token before and after; a wrong-answer rate; an isolation test that passes |
| Hosting analysis | 20 | The register read first; capacity at the latency objective; a break-even chart against the right alternative |
| Review quality | 15 | Two pages a finance partner can act on: a total that the invoice can show, owners, a refusal, energy with its source |

The capstone repository counts for 60% of the course result, and you need at least 60% on this rubric. The live
defence counts for 20%. The supervised check without AI assistance, on cost arithmetic and caching trade-offs,
counts for the other 20%. The pass mark is 70% overall.

## The defence · ten minutes

1. **Two minutes:** the month in three numbers and the decision you ask for.
2. **Five minutes:** the assessor picks one savings figure of your review. You recompute it from the log on your
   own screen and say what it includes and what it leaves out.
3. **Three minutes:** you explain one routing decision the assessor selects: which requests go where, what the check misses, and what
   would make you change it.

**AI policy.** AI assistance is allowed for the repository and the review. Keep the assistant's transcripts with
their timestamps: together with the defence they are the evidence of authorship. During the defence you work
without an assistant.
