"""Publish governance (pure, deterministic): a post is outward-facing and effectively irreversible,
so publishing is gated (ADR-0054). Two independent gates decide whether a human must approve: the
brand's ``review_mode`` (human-approval-first-N / always / never) and the **authority** check via
``ab_org`` (does any agent hold the level this action needs, or does it escalate to a person?). A
separate deterministic boost policy decides whether to spend on amplification via ``ab_ads``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_org.core import Org, route
from ab_schemas.events import ContentPublished
from ab_social.core import Draft, PublisherLike, qa, to_event
from ab_social.profile import ReviewMode, SocialProfile


@dataclass(frozen=True)
class PublishAuthorization:
    requires_human: bool
    reason: str


def _review_requires_human(profile: SocialProfile, posts_published_so_far: int) -> bool:
    if profile.review_mode is ReviewMode.ALWAYS:
        return True
    if profile.review_mode is ReviewMode.NEVER:
        return False
    return posts_published_so_far < profile.review_first_n  # HUMAN_APPROVAL_FIRST_N


def authorize_publish(
    profile: SocialProfile,
    *,
    posts_published_so_far: int,
    initiator: str,
    org: Org,
    required_level: int,
) -> PublishAuthorization:
    """Decide whether a human must approve this publish: required if the review mode says so OR the
    authority chain escalates to a human (no agent holds ``required_level``)."""
    reasons: list[str] = []
    if _review_requires_human(profile, posts_published_so_far):
        reasons.append(f"review_mode {profile.review_mode.value}")
    if route(org, initiator=initiator, required_level=required_level).escalated_to_human:
        reasons.append(f"authority: no agent holds level {required_level}")
    return PublishAuthorization(requires_human=bool(reasons), reason="; ".join(reasons) or "autonomous")


def governed_publish(
    draft: Draft,
    profile: SocialProfile,
    publisher: PublisherLike,
    *,
    authorization: PublishAuthorization,
    human_approved: bool = False,
) -> ContentPublished | None:
    """Publish only when authorised: if a human is required and hasn't approved, the post is HELD
    (returns None, nothing published); otherwise it goes through QA and the publisher port."""
    if authorization.requires_human and not human_approved:
        return None
    if not qa(draft, profile).passed:
        return None
    result = publisher.publish(draft)
    return to_event(draft, result.platform_post_id)


def should_boost(
    composite_score_bps: int,
    *,
    min_score_bps: int,
    boost_cost_minor: int,
    budget_remaining_minor: int,
) -> bool:
    """Deterministic boost policy: amplify a post only if it's a proven performer (score at/above the
    threshold) and the boost fits the remaining budget. Boosts run through ``ab_ads``."""
    return composite_score_bps >= min_score_bps and 0 < boost_cost_minor <= budget_remaining_minor
