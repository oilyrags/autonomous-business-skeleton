"""The experiment decision engine: every SCALE / PIVOT / KILL / CONTINUE path, per business."""

import pytest

from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Action, Experiment, Variant, decide, to_event

BP = Blueprint(
    business_id="acme",
    name="Acme",
    target_revenue_minor=1_000_000,
    experiment_budget_minor=200_000,
    min_conversion_rate=0.04,
    max_cac_minor=5_000,
    min_exposure_per_arm=1000,
)


def _exp(cv: tuple[int, int, int], vv: tuple[int, int, int], eid: str = "e1") -> Experiment:
    return Experiment(
        experiment_id=eid,
        business_id="acme",
        hypothesis="h",
        control=Variant(name="c", impressions=cv[0], conversions=cv[1], spend_minor=cv[2]),
        variant=Variant(name="v", impressions=vv[0], conversions=vv[1], spend_minor=vv[2]),
    )


def test_variant_rejects_more_conversions_than_impressions() -> None:
    with pytest.raises(ValueError):
        Variant(name="x", impressions=10, conversions=11, spend_minor=0)


def test_cac_is_none_without_conversions() -> None:
    assert Variant(name="x", impressions=100, conversions=0, spend_minor=500).cac_minor is None


def test_significant_win_meeting_kpi_scales() -> None:
    d = decide(_exp((2000, 60, 800_00), (2000, 130, 900_00)), BP)  # 3% -> 6.5%, CAC ~692
    assert d.action is Action.SCALE and d.lift > 0


def test_cac_breach_kills_regardless() -> None:
    d = decide(_exp((2000, 60, 800_00), (2000, 12, 900_00)), BP)  # CAC 7500 > 5000
    assert d.action is Action.KILL and "CAC" in d.reason


def test_significant_lift_below_kpi_pivots() -> None:
    d = decide(_exp((5000, 100, 800_00), (5000, 175, 900_00)), BP)  # 2% -> 3.5% (<4% KPI)
    assert d.action is Action.PIVOT


def test_significantly_worse_kills() -> None:
    d = decide(_exp((3000, 180, 800_00), (3000, 90, 900_00)), BP)  # 6% -> 3%
    assert d.action is Action.KILL and "worse" in d.reason


def test_underpowered_within_budget_continues() -> None:
    d = decide(_exp((200, 12, 200_00), (200, 16, 250_00)), BP)  # tiny sample, spend < budget
    assert d.action is Action.CONTINUE


def test_inconclusive_out_of_budget_kills() -> None:
    d = decide(_exp((800, 20, 1000_00), (800, 26, 1200_00)), BP)  # not sig, total spend > budget
    assert d.action is Action.KILL and "budget" in d.reason


def test_decision_event_is_business_scoped() -> None:
    exp = _exp((2000, 60, 800_00), (2000, 130, 900_00))
    ev = to_event(exp, decide(exp, BP))
    assert ev.event_name == "ExperimentConcluded"
    assert ev.business_id == "acme" and ev.action == "scale"
    assert ev.variant_rate > ev.control_rate
