"""Experiment KPI projections (PRD 0007 E6): fold the experiments store into per-business fleet
metrics, and render them as Prometheus gauges. Pure — the console's `/metrics` (M5 rail) exposes
them so one definition feeds both the console and Grafana. `business_id`-scoped (multi-tenancy).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ab_growth.store import ExperimentRecord


@dataclass(frozen=True)
class ExperimentKpi:
    business_id: str
    open: int  # proposed/running
    concluded: int
    scaled: int  # concluded with a SCALE decision
    win_rate_bps: int  # scaled / concluded, in basis points (0 when nothing concluded)
    budget_committed_minor: int


def experiment_kpis(records: Iterable[ExperimentRecord]) -> list[ExperimentKpi]:
    """Per-business experiment KPIs, sorted by business_id for determinism."""
    acc: dict[str, dict[str, int]] = {}
    for r in records:
        b = acc.setdefault(r.business_id, {"open": 0, "concluded": 0, "scaled": 0, "budget": 0})
        b["budget"] += r.budget_minor
        if r.status == "concluded":
            b["concluded"] += 1
            if r.decision == "scale":
                b["scaled"] += 1
        else:
            b["open"] += 1
    return [
        ExperimentKpi(
            business_id=bid,
            open=v["open"],
            concluded=v["concluded"],
            scaled=v["scaled"],
            win_rate_bps=round(10_000 * v["scaled"] / v["concluded"]) if v["concluded"] else 0,
            budget_committed_minor=v["budget"],
        )
        for bid, v in sorted(acc.items())
    ]


def experiment_gauges(kpis: Iterable[ExperimentKpi]) -> list[str]:
    """Render the KPIs as Prometheus gauge lines (business_id-labelled), with HELP/TYPE headers."""
    specs = (
        ("ab_experiment_open", "Proposed/running experiments.", "open"),
        ("ab_experiment_concluded", "Concluded experiments.", "concluded"),
        ("ab_experiment_scaled", "Experiments concluded with a SCALE decision.", "scaled"),
        ("ab_experiment_win_rate_bps", "Scaled / concluded, in basis points.", "win_rate_bps"),
        (
            "ab_experiment_budget_committed_minor",
            "Total experiment budget committed (minor units).",
            "budget_committed_minor",
        ),
    )
    kpis = list(kpis)
    lines: list[str] = []
    for name, help_text, attr in specs:
        lines += [f"# HELP {name} {help_text}", f"# TYPE {name} gauge"]
        lines += [f'{name}{{business_id="{k.business_id}"}} {getattr(k, attr)}' for k in kpis]
    return lines
