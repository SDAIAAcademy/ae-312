"""Generate the data of a capstone scenario: another month at Mawj Telecom (synthetic).

    uv run python capstone/make_scenario.py b                 # writes labs/artifacts/capstone/b/data
    uv run python capstone/make_scenario.py b --out ../my-review/data

Then point the helpers at it:  MAWJ_DATA=<that folder>  (see capstone/README.md).
The scenarios use the generator of the course with another seed and other volumes, so no number of the three
teaching days carries over: every figure in the review has to be measured again.
"""
import argparse
import json
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LABS))

import prepare_data  # noqa: E402

SCENARIOS = {
    "a": {
        "title": "The care assistant doubles",
        "brief": "A campaign doubles the traffic of Anis for the month. A larger share of the spend bypasses the gateway, "
                 "and the incident falls early in the month.",
        "knobs": dict(seed=3121, anis_sessions=36000, incident_day=9, direct_share=0.04),
    },
    "b": {
        "title": "The call-summary job triples",
        "brief": "Khulasa now summarises three times as many calls, the pilot on the leased node has grown with it and "
                 "the node is leased twelve hours a night. Finance asks again whether Mawj should host the model itself.",
        "knobs": dict(seed=3122, khulasa_calls=78000, pilot_requests=14000, node_hours_per_night=12, incident_day=21),
    },
    "c": {
        "title": "The dispute agent rolls out",
        "brief": "Fasil handles twice as many disputes, and the cheaper configuration has been taking most of them "
                 "since the second week. Billing operations reports more reopened disputes.",
        "knobs": dict(seed=3123, fasil_sessions=6400, fasil_b_from_day=8, fasil_b_share=0.7, incident_day=24),
    },
}


def make(letter, out=None):
    s = SCENARIOS[letter]
    out = Path(out) if out else LABS / "artifacts" / "capstone" / letter / "data"
    files = prepare_data.build(out, **s["knobs"])
    (out / "scenario.json").write_text(json.dumps({"scenario": letter, "title": s["title"], "brief": s["brief"], "synthetic": True}, indent=1) + "\n", encoding="utf-8")
    return out, len(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out, n = make(a.scenario, a.out)
    print(f"scenario {a.scenario}: {SCENARIOS[a.scenario]['title']}\n{SCENARIOS[a.scenario]['brief']}\nwrote {n} files to {out}")


if __name__ == "__main__":
    main()
