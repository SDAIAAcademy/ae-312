"""Figures of the parallel examples on committed capacity against on-demand hours (Day 3, session 1).

    uv run python _tools/commitment_examples.py      # from labs/

Synthetic numbers for a team that is not Mawj, so that no figure on the slides or in the practice question is an
answer of Lab 3.1. A commitment is paid every month of its term, used or not; on-demand hours are paid as used.
"""

from __future__ import annotations

HOURS_IN_MONTH = 744


def break_even_hours(commitment_per_month: float, on_demand_per_hour: float) -> float:
    """Leased hours a month above which the commitment costs less than the same hours on demand."""
    return commitment_per_month / on_demand_per_hour


def slides() -> None:
    on_demand, commitment = 20.0, 8400.0
    be = break_even_hours(commitment, on_demand)
    rate = commitment / HOURS_IN_MONTH
    print("Slides: on demand SAR", on_demand, "an hour; 12-month commitment SAR", commitment, "a month")
    print(f"  committed hourly rate {rate:.2f}, discount {1 - rate / on_demand:.1%}")
    print(f"  break-even {be:.0f} leased hours a month, {be / HOURS_IN_MONTH:.1%} of the month")
    workloads = {
        "A, support assistant, 16 hours a day": [492, 470, 505, 488, 476, 498],
        "B, evaluation runs": [610, 150, 520, 90, 380, 330],
        "C, a model being retired": [560, 510, 455, 430, 390, 350],
    }
    for name, hours in workloads.items():
        od = sum(hours) * on_demand
        cm = len(hours) * commitment
        above = sum(h > be for h in hours)
        print(f"  {name}: lowest {min(hours)}, average {sum(hours) / len(hours):.0f}, months above break-even {above} of 6; "
              f"six months on demand {od:,.0f} against committed {cm:,.0f} (commitment {'saves' if cm < od else 'costs'} {abs(od - cm):,.0f})")
        last = hours[-1]
        print(f"    at the last month's {last} hours: on demand {last * on_demand:,.0f} against {commitment:,.0f} a month")


def bank() -> None:
    on_demand, commitment = 16.0, 7200.0
    hours = [380, 395, 372, 410, 388, 401]
    be = break_even_hours(commitment, on_demand)
    rate = commitment / HOURS_IN_MONTH
    print("Bank item q-host-04: on demand SAR", on_demand, "; commitment SAR", commitment, "a month")
    print(f"  committed hourly rate {rate:.2f}; break-even {be:.0f} hours; months {hours}, highest {max(hours)}, "
          f"average {sum(hours) / len(hours):.0f}; on demand the busiest month costs {max(hours) * on_demand:,.0f} "
          f"and a month at the average {sum(hours) / len(hours) * on_demand:,.0f}")


if __name__ == "__main__":
    slides()
    bank()
