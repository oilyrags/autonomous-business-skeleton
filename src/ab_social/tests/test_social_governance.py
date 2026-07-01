"""Publish governance: review modes + ab_org authority gate + boost policy (pure, infra-free)."""

from __future__ import annotations

from ab_ads.core import AdCampaign, run_campaigns
from ab_ads.platform import StubAdPlatform
from ab_ledger.core import InMemoryLedger
from ab_org.core import Charter, Org
from ab_social.core import Draft, plan
from ab_social.generator import StubContentGenerator
from ab_social.governance import authorize_publish, governed_publish, should_boost
from ab_social.profile import Pillar, PlatformConfig, PostingRules, ReviewMode, SocialProfile
from ab_social.publisher import StubPublisher

ORG = Org(
    charters={
        "social": Charter("social", "Social Agent", 2, "marketing", reports_to="cmo"),
        "cmo": Charter("cmo", "CMO", 3, "marketing", reports_to=None),
    }
)


def _profile(mode: ReviewMode = ReviewMode.NEVER, *, first_n: int = 3) -> SocialProfile:
    return SocialProfile(
        business_id="acme",
        voice="v",
        pillars=(Pillar(name="Productivity", weight=1.0),),
        platforms=(PlatformConfig(name="x", format_mix={"text_post": 1.0}),),
        posting_rules=PostingRules(required_elements=("cta_or_question", "relevant_hashtags_or_keywords")),
        review_mode=mode,
        review_first_n=first_n,
    )


def _draft(profile: SocialProfile) -> Draft:
    return StubContentGenerator().write(plan(profile, count=1)[0], profile)


def test_never_mode_within_authority_is_autonomous() -> None:
    auth = authorize_publish(
        _profile(ReviewMode.NEVER), posts_published_so_far=100, initiator="social", org=ORG, required_level=2
    )
    assert auth.requires_human is False


def test_always_mode_requires_human() -> None:
    auth = authorize_publish(
        _profile(ReviewMode.ALWAYS), posts_published_so_far=100, initiator="social", org=ORG, required_level=2
    )
    assert auth.requires_human is True


def test_first_n_gates_only_the_first_n_posts() -> None:
    p = _profile(ReviewMode.HUMAN_APPROVAL_FIRST_N, first_n=3)
    early = authorize_publish(p, posts_published_so_far=1, initiator="social", org=ORG, required_level=2)
    later = authorize_publish(p, posts_published_so_far=5, initiator="social", org=ORG, required_level=2)
    assert early.requires_human is True and later.requires_human is False


def test_authority_escalation_forces_human_even_in_never_mode() -> None:
    # No agent holds level 5 -> escalates to a human regardless of review mode.
    auth = authorize_publish(
        _profile(ReviewMode.NEVER), posts_published_so_far=100, initiator="social", org=ORG, required_level=5
    )
    assert auth.requires_human is True and "authority" in auth.reason


def test_governed_publish_holds_until_human_approves() -> None:
    profile = _profile(ReviewMode.ALWAYS)
    draft = _draft(profile)
    auth = authorize_publish(profile, posts_published_so_far=0, initiator="social", org=ORG, required_level=2)
    assert governed_publish(draft, profile, StubPublisher(), authorization=auth) is None  # held
    approved = governed_publish(draft, profile, StubPublisher(), authorization=auth, human_approved=True)
    assert approved is not None and approved.event_name == "ContentPublished"


def test_boost_policy_amplifies_only_proven_posts_within_budget() -> None:
    assert should_boost(600, min_score_bps=400, boost_cost_minor=5_000, budget_remaining_minor=10_000) is True
    assert (
        should_boost(200, min_score_bps=400, boost_cost_minor=5_000, budget_remaining_minor=10_000) is False
    )
    assert (
        should_boost(600, min_score_bps=400, boost_cost_minor=20_000, budget_remaining_minor=10_000) is False
    )


def test_a_boost_books_ad_spend_through_ab_ads() -> None:
    led = InMemoryLedger()
    if should_boost(600, min_score_bps=400, boost_cost_minor=8_000, budget_remaining_minor=50_000):
        run_campaigns(
            StubAdPlatform(cost_per_conversion_minor=1_000),
            [AdCampaign(business_id="acme", spend_minor=8_000, channel="boost", external_ref="b1")],
            led,
        )
    assert led.business_spend("acme").external_spend_minor == 8_000  # boost is real ledger money
    assert led.trial_balance() == 0
