"""Fold ExperimentConcluded events into per-business performance (pure, no I/O).

The growth context publishes ``ExperimentConcluded`` (scale/pivot/kill/continue). This tallies
those outcomes per ``business_id`` into the ``BusinessPerformance`` that ``allocate`` consumes —
capital comes from the ledger (injected), never re-derived from events.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ab_portfolio.core import BusinessPerformance
from ab_schemas.events import ExperimentConcluded

_CONCLUSIVE = ("scale", "pivot", "kill")


def rollup(
    events: Iterable[ExperimentConcluded],
    *,
    capital_by_business: Mapping[str, int],
) -> list[BusinessPerformance]:
    """Tally concluded outcomes per business into performances (first-seen order)."""
    tallies: dict[str, dict[str, int]] = {}
    for e in events:
        if e.action not in _CONCLUSIVE:
            continue  # ``continue`` is not a conclusion — the experiment is still running
        t = tallies.setdefault(e.business_id, {"scale": 0, "pivot": 0, "kill": 0})
        t[e.action] += 1
    return [
        BusinessPerformance(
            business_id=bid,
            capital_minor=capital_by_business.get(bid, 0),
            scale_count=t["scale"],
            pivot_count=t["pivot"],
            kill_count=t["kill"],
        )
        for bid, t in tallies.items()
    ]
