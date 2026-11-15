# AI Cost Engineering and Model Routing: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository.
- Locally: clone the repository, then open the notebooks in `labs/` with Jupyter.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · The token cost model | [`D1_1_compute_cost_per.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_1_compute_cost_per.ipynb) |
| Day 1 | Session 2 · Agents, retries and long contexts | [`D1_2_find_ten_most.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_2_find_ten_most.ipynb) |
| Day 1 | Session 3 · Attribution and showback | [`D1_3_tag_spend_team.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_3_tag_spend_team.ipynb) |
| Day 1 | Session 4 · Budgets and limits | [`D1_4_set_soft_hard.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D1_4_set_soft_hard.ipynb) |
| Day 2 | Session 1 · Own tasks, several settings | [`D2_1_score_supplied_outputs.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_1_score_supplied_outputs.ipynb) |
| Day 2 | Session 2 · Routing and cascades | [`D2_2_build_two_tier.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_2_build_two_tier.ipynb) |
| Day 2 | Session 3 · Prompt layout for prefix caching | [`D2_3_move_stable_content.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_3_move_stable_content.ipynb) |
| Day 2 | Session 4 · Semantic caches and their risks | [`D2_4_add_semantic_cache.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D2_4_add_semantic_cache.ipynb) |
| Day 3 | Session 1 · Self-hosting economics | [`D3_1_fill_cost_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_1_fill_cost_model.ipynb) |
| Day 3 | Session 2 · Batch versus interactive | [`D3_2_move_call_summary.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_2_move_call_summary.ipynb) |
| Day 3 | Session 3 · Cost per successful outcome | [`D3_3_join_cost_evaluation.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_3_join_cost_evaluation.ipynb) |
| Day 3 | Session 4 · The cost review | [`D3_4_draft_two_page.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-312/blob/main/labs/D3_4_draft_two_page.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.
