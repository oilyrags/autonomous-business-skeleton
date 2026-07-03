"""Experiment KPI projections (PRD 0007 E6): per-business fleet metrics from the experiments store,
surfaced through the Prometheus rail. Pure + infra-free."""

from __future__ import annotations

from ab_growth.kpis import ExperimentKpi, experiment_gauges, experiment_kpis
from ab_growth.store import ExperimentRecord


def _rec(business_id: str, status: str, decision: str | None, budget: int) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id=f"e-{business_id}-{status}-{decision}",
        business_id=business_id,
        hypothesis="h",
        arm_names=["control", "treatment"],
        budget_minor=budget,
        status=status,
        decision=decision,
    )


def test_experiment_kpis_are_computed_per_business() -> None:
    records = [
        _rec("rocket", "concluded", "scale", 50_000),
        _rec("rocket", "concluded", "kill", 50_000),
        _rec("rocket", "proposed", None, 80_000),
        _rec("hog", "running", None, 20_000),
    ]
    by_id = {k.business_id: k for k in experiment_kpis(records)}

    rocket = by_id["rocket"]
    assert rocket.open == 1 and rocket.concluded == 2 and rocket.scaled == 1
    assert rocket.win_rate_bps == 5000  # 1 of 2 concluded → 50% → 5000 bps
    assert rocket.budget_committed_minor == 180_000

    hog = by_id["hog"]
    assert hog.open == 1 and hog.concluded == 0
    assert hog.win_rate_bps == 0  # nothing concluded → no division by zero


def test_experiment_gauges_are_business_scoped_prometheus_lines() -> None:
    kpi = ExperimentKpi(
        business_id="rocket",
        open=1,
        concluded=2,
        scaled=1,
        win_rate_bps=5000,
        budget_committed_minor=180_000,
    )
    lines = experiment_gauges([kpi])
    assert 'ab_experiment_open{business_id="rocket"} 1' in lines
    assert 'ab_experiment_concluded{business_id="rocket"} 2' in lines
    assert 'ab_experiment_win_rate_bps{business_id="rocket"} 5000' in lines
    assert 'ab_experiment_budget_committed_minor{business_id="rocket"} 180000' in lines
