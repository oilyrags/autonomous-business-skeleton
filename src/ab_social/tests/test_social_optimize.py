"""Self-optimization: a winning pillar (via ab_growth) reweights the SocialProfile (pure)."""

from __future__ import annotations

import pytest

from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Action
from ab_social.metrics import PostMetrics
from ab_social.optimize import distil_winning_pillars, reweight, run_optimization
from ab_social.profile import Pillar, PlatformConfig, SocialProfile


def _profile() -> SocialProfile:
    return SocialProfile(
        business_id="acme",
        voice="v",
        pillars=(Pillar(name="Productivity", weight=0.4), Pillar(name="Insights", weight=0.4)),
        platforms=(PlatformConfig(name="linkedin", format_mix={"carousel": 1.0}),),
    )


def _blueprint() -> Blueprint:
    return Blueprint(
        business_id="acme",
        name="Acme",
        target_revenue_minor=1_000_000,
        experiment_budget_minor=1_000_000,
        min_conversion_rate=0.05,
        max_cac_minor=1_000_000,
        significance_alpha=0.05,
        min_exposure_per_arm=1_000,
    )


def _posts(engagement_per_1000: int, n: int = 3) -> list[PostMetrics]:
    return [
        PostMetrics(
            business_id="acme",
            platform_post_id=f"p{i}",
            impressions=1_000,
            likes=engagement_per_1000,
        )
        for i in range(n)
    ]


def test_reweight_scales_one_pillars_weight() -> None:
    p = reweight(_profile(), "Productivity", factor=1.5)
    weights = {pl.name: pl.weight for pl in p.pillars}
    assert weights["Productivity"] == pytest.approx(0.6)  # 0.4 * 1.5
    assert weights["Insights"] == 0.4  # untouched


def test_a_clear_winner_is_scaled_and_bumps_the_profile() -> None:
    decision, updated = run_optimization(
        _profile(),
        _blueprint(),
        incumbent_pillar="Insights",
        challenger_pillar="Productivity",
        incumbent_posts=_posts(40),  # 4% engagement
        challenger_posts=_posts(120),  # 12% engagement — a significant win over the 5% KPI
    )
    assert decision.action is Action.SCALE
    weights = {pl.name: pl.weight for pl in updated.pillars}
    assert weights["Productivity"] == pytest.approx(0.6)  # scaled up from 0.4


def test_distil_winning_pillars_finds_the_common_lead() -> None:
    def brand(bid: str, lead: str) -> SocialProfile:
        others = "Insights" if lead == "Productivity" else "Productivity"
        return SocialProfile(
            business_id=bid,
            voice="v",
            pillars=(Pillar(name=lead, weight=0.7), Pillar(name=others, weight=0.3)),
            platforms=(PlatformConfig(name="x", format_mix={"text_post": 1.0}),),
        )

    winners = [brand("a", "Productivity"), brand("b", "Productivity"), brand("c", "Insights")]
    assert distil_winning_pillars(winners, min_brands=2) == ("Productivity",)
