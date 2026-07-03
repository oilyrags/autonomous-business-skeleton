"""The growth runner (PRD 0007 E3): assemble live arm stats → deterministic decide → outcome.

Pure tests here; the create→run→conclude persistence loop is infra-gated (test_runner_loop.py-style,
kept alongside the gateway integration tests). The verdict is always `ab_growth.decide` — the runner
never makes the money/guardrail call itself (ADR-0058 decision 2)."""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_growth.runner import ArmStats, run
from ab_growth.store import ExperimentRecord


def _record(budget_minor: int = 200_000) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id="exp-1",
        business_id="rocket",
        hypothesis="a shorter headline lifts signups",
        arm_names=["control", "treatment"],
        budget_minor=budget_minor,
        status="proposed",
    )


def _blueprint() -> Blueprint:
    return Blueprint(
        business_id="rocket",
        name="rocket",
        target_revenue_minor=5_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
    )


def test_run_scales_a_significant_win_within_budget() -> None:
    decision = run(
        _record(),
        _blueprint(),
        control=ArmStats(impressions=1_000, conversions=40, spend_minor=30_000),
        variant=ArmStats(impressions=1_000, conversions=120, spend_minor=30_000),  # 12% vs 4%, p≈0
    )
    assert decision.action.value == "scale"


def test_per_experiment_budget_cap_concludes_even_below_the_blueprint_budget() -> None:
    # Inconclusive arms (5.0% vs 5.2%), blueprint budget is 200_000, but the operator capped this
    # experiment at 50_000 and it has already spent 60_000 → the cap forces a KILL, not a CONTINUE.
    decision = run(
        _record(budget_minor=50_000),
        _blueprint(),
        control=ArmStats(impressions=1_000, conversions=50, spend_minor=30_000),
        variant=ArmStats(impressions=1_000, conversions=52, spend_minor=30_000),
    )
    assert decision.action.value == "kill"
    assert "budget" in decision.reason.lower()
