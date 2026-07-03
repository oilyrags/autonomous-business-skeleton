"""Post metrics + composite scoring (pure, deterministic). A ``MetricsSource`` port fetches a
post's raw engagement counts (stub by default; a real platform-analytics adapter behind the same
interface); ``composite_score`` blends the normalized KPIs by the brand's ``kpi_weights`` into one
integer basis-points score, so posts are comparable across platforms and can drive the growth loop.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from pydantic import BaseModel, Field

from ab_schemas.events import PostMetricsCollected, build


class PostMetrics(BaseModel):
    business_id: str
    platform_post_id: str
    impressions: int = Field(ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    follows: int = Field(default=0, ge=0)


class MetricsSource(Protocol):
    """Fetch a published post's engagement metrics by its platform post id."""

    def metrics(self, platform_post_id: str) -> PostMetrics: ...


class StubMetricsSource:
    """Deterministic metrics for tests + the demo, keyed by platform post id. A real platform-
    analytics adapter implements the same ``metrics``."""

    def __init__(self, by_id: dict[str, PostMetrics]) -> None:
        self._by_id = dict(by_id)

    def metrics(self, platform_post_id: str) -> PostMetrics:
        return self._by_id[platform_post_id]


def kpi_values(m: PostMetrics) -> dict[str, float]:
    """Normalized KPI ratios from raw counts (0 when there are no impressions)."""
    imp = m.impressions
    if imp == 0:
        return {"engagement_rate": 0.0, "comments_quality": 0.0, "link_clicks": 0.0, "follower_growth": 0.0}
    return {
        "engagement_rate": (m.likes + m.comments + m.shares) / imp,
        "comments_quality": m.comments / imp,
        "link_clicks": m.clicks / imp,
        "follower_growth": m.follows / imp,
    }


def composite_score(m: PostMetrics, kpi_weights: Mapping[str, float]) -> int:
    """The single KPI-weighted score for a post, in integer basis points. Weights are normalized by
    their sum; unknown KPI names contribute 0."""
    values = kpi_values(m)
    total_weight = sum(kpi_weights.values()) or 1.0
    blended = sum(w / total_weight * values.get(name, 0.0) for name, w in kpi_weights.items())
    return round(blended * 10_000)


def to_event(
    m: PostMetrics, score_bps: int, *, producer: str = "marketing.social_agent"
) -> PostMetricsCollected:
    return build(
        PostMetricsCollected,
        subject=("Business", m.business_id),
        producer=producer,
        business_id=m.business_id,
        platform_post_id=m.platform_post_id,
        impressions=m.impressions,
        composite_score_bps=score_bps,
    )


def collect_metrics(
    platform_post_id: str, source: MetricsSource, kpi_weights: Mapping[str, float]
) -> PostMetricsCollected:
    """Fetch a post's metrics from the source, score them, and return the event."""
    m = source.metrics(platform_post_id)
    return to_event(m, composite_score(m, kpi_weights))
