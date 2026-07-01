"""Living Playbooks: distil winners into a reusable blueprint, then instantiate from it (pure)."""

from __future__ import annotations

import pytest

from ab_growth.blueprint import Blueprint
from ab_playbook.core import apply_playbook, extract_playbook


def _bp(bid: str, *, cac: int, rate: float, modules: tuple[str, ...]) -> Blueprint:
    return Blueprint(
        business_id=bid,
        name=bid.title(),
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=rate,
        max_cac_minor=cac,
        enabled_modules=modules,
    )


WINNERS = [
    _bp("a", cac=3_000, rate=0.04, modules=("waitlist", "checkout")),
    _bp("b", cac=5_000, rate=0.06, modules=("waitlist", "referral")),
    _bp("c", cac=4_000, rate=0.05, modules=("waitlist", "checkout")),
]


def test_playbook_takes_the_median_economics() -> None:
    pb = extract_playbook(WINNERS, version="v1")
    assert pb.max_cac_minor == 4_000  # median of 3_000, 5_000, 4_000
    assert pb.min_conversion_rate == 0.05  # median of 0.04, 0.06, 0.05
    assert pb.sample_size == 3


def test_recommended_modules_are_the_majority_used() -> None:
    pb = extract_playbook(WINNERS, version="v1")
    # waitlist in 3/3, checkout in 2/3 (majority = 2); referral in 1/3 (not).
    assert pb.recommended_modules == ("waitlist", "checkout")


def test_playbook_carries_only_aggregates_no_business_ids() -> None:
    pb = extract_playbook(WINNERS, version="v1")
    assert pb.module_frequency == {"waitlist": 3, "checkout": 2, "referral": 1}  # aggregate counts
    # the playbook has no per-business field — learning transfers without any business_id
    assert not hasattr(pb, "business_id")


def test_apply_playbook_instantiates_a_new_blueprint() -> None:
    pb = extract_playbook(WINNERS, version="v1")
    bp = apply_playbook(pb, business_id="newco", name="NewCo")
    assert bp.business_id == "newco"
    assert bp.max_cac_minor == 4_000
    assert bp.enabled_modules == ("waitlist", "checkout")


def test_extract_requires_at_least_one_winner() -> None:
    with pytest.raises(ValueError, match="zero winners"):
        extract_playbook([], version="v1")
