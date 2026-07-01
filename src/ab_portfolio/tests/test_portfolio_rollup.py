"""Rollup of ExperimentConcluded events into per-business performance (pure, no I/O)."""

from __future__ import annotations

from datetime import UTC, datetime

from ab_portfolio.rollup import rollup
from ab_schemas.events import DataClassification, ExperimentConcluded, SubjectRef


def _concluded(business_id: str, action: str, *, experiment_id: str = "exp") -> ExperimentConcluded:
    return ExperimentConcluded(
        event_name="ExperimentConcluded",
        event_id=f"{business_id}-{experiment_id}-{action}",
        occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
        producer="growth.experiment_agent",
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="Experiment", id=experiment_id),
        business_id=business_id,
        experiment_id=experiment_id,
        action=action,
        reason="test",
        p_value=0.01,
        control_rate=0.1,
        variant_rate=0.2,
    )


def test_single_scale_event_becomes_one_performance() -> None:
    perfs = rollup([_concluded("rocket", "scale")], capital_by_business={"rocket": 100_000})
    assert len(perfs) == 1
    p = perfs[0]
    assert p.business_id == "rocket"
    assert p.scale_count == 1
    assert p.capital_minor == 100_000


def test_mixed_outcomes_for_one_business_tally_and_score() -> None:
    events = [
        _concluded("mix", "scale", experiment_id="a"),
        _concluded("mix", "scale", experiment_id="b"),
        _concluded("mix", "pivot", experiment_id="c"),
        _concluded("mix", "kill", experiment_id="d"),
    ]
    (p,) = rollup(events, capital_by_business={"mix": 50_000})
    assert (p.scale_count, p.pivot_count, p.kill_count) == (2, 1, 1)
    assert p.score == 1  # 2 scale − 1 kill
    assert p.experiments == 4


def test_two_businesses_isolated_and_in_first_seen_order() -> None:
    events = [
        _concluded("beta", "kill", experiment_id="a"),
        _concluded("alpha", "scale", experiment_id="b"),
        _concluded("beta", "kill", experiment_id="c"),
    ]
    perfs = rollup(events, capital_by_business={"alpha": 1, "beta": 2})
    assert [p.business_id for p in perfs] == ["beta", "alpha"]
    beta, alpha = perfs
    assert beta.kill_count == 2
    assert alpha.scale_count == 1


def test_continue_events_are_ignored() -> None:
    perfs = rollup([_concluded("waiting", "continue")], capital_by_business={"waiting": 10_000})
    assert perfs == []


def test_missing_capital_defaults_to_zero() -> None:
    (p,) = rollup([_concluded("orphan", "scale")], capital_by_business={})
    assert p.capital_minor == 0
