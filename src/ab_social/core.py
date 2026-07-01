"""Social content core (pure, deterministic): decide *what* to post (the plan), gate *whether* a
draft is fit to publish (QA / brand-safety), and publish a passing draft through the injected
Publisher port. The LLM (behind ``ContentGenerator``) only writes the copy; every decision here is
deterministic, in the ``ab_growth``/``ab_econ`` style. No I/O.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel

from ab_schemas.events import ContentPublished, DataClassification, SubjectRef
from ab_social.profile import SocialProfile


class ContentPlanItem(BaseModel):
    business_id: str
    pillar: str
    platform: str
    format: str
    key_message: str


class Draft(BaseModel):
    business_id: str
    platform: str
    format: str
    pillar: str
    body: str
    hashtags: tuple[str, ...]
    has_cta: bool


@dataclass(frozen=True)
class QaResult:
    passed: bool
    reasons: tuple[str, ...]


class PublisherLike(Protocol):
    def publish(self, draft: Draft) -> PublishResultLike: ...


class PublishResultLike(Protocol):
    platform: str
    platform_post_id: str


def _allocate(weights: list[float], count: int) -> list[int]:
    """Largest-remainder allocation of ``count`` slots across weighted pillars (deterministic)."""
    total = sum(weights) or 1.0
    raw = [w / total * count for w in weights]
    floors = [int(x) for x in raw]
    remainder = count - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i] - floors[i]), i))
    for i in order[:remainder]:
        floors[i] += 1
    return floors


def plan(profile: SocialProfile, *, count: int) -> list[ContentPlanItem]:
    """Draw a deterministic content plan: allocate posts across pillars by weight, cycle platforms,
    and pick each platform's top-share format. Same profile + count → same plan."""
    alloc = _allocate([p.weight for p in profile.pillars], count)
    items: list[ContentPlanItem] = []
    platform_idx = 0
    for pillar, n in zip(profile.pillars, alloc, strict=True):
        for _ in range(n):
            platform = profile.platforms[platform_idx % len(profile.platforms)]
            platform_idx += 1
            top_format = max(platform.format_mix.items(), key=lambda kv: (kv[1], kv[0]))[0]
            items.append(
                ContentPlanItem(
                    business_id=profile.business_id,
                    pillar=pillar.name,
                    platform=platform.name,
                    format=top_format,
                    key_message=f"{pillar.name} for {profile.business_id}",
                )
            )
    return items


def qa(draft: Draft, profile: SocialProfile) -> QaResult:
    """Brand-safety / posting-rules gate: reject a draft that uses a forbidden term or omits a
    required element. Deterministic — the guardrail an off-brand post cannot pass."""
    reasons: list[str] = []
    body_lower = draft.body.lower()
    for term in profile.posting_rules.forbidden:
        if term.lower() in body_lower:
            reasons.append(f"forbidden term '{term}'")
    for element in profile.posting_rules.required_elements:
        if element == "cta_or_question" and not (draft.has_cta or "?" in draft.body):
            reasons.append("missing cta or question")
        elif element == "relevant_hashtags_or_keywords" and not draft.hashtags:
            reasons.append("missing hashtags/keywords")
    return QaResult(passed=not reasons, reasons=tuple(reasons))


def to_event(
    draft: Draft, platform_post_id: str, *, producer: str = "marketing.social_agent"
) -> ContentPublished:
    return ContentPublished(
        event_name="ContentPublished",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="Business", id=draft.business_id),
        business_id=draft.business_id,
        platform=draft.platform,
        platform_post_id=platform_post_id,
        format=draft.format,
        pillar=draft.pillar,
    )


def publish_content(
    draft: Draft, profile: SocialProfile, publisher: PublisherLike
) -> ContentPublished | None:
    """Gate a draft through QA, then publish it via the port. Returns the ``ContentPublished`` event
    on success, or ``None`` if QA rejected it (nothing is published). Governance depth (review mode,
    authority gate, cost metering) layers on in a later slice."""
    if not qa(draft, profile).passed:
        return None
    result = publisher.publish(draft)
    return to_event(draft, result.platform_post_id)
