"""Post metrics + composite scoring (pure, infra-free)."""

from __future__ import annotations

from ab_social.metrics import PostMetrics, StubMetricsSource, collect_metrics, composite_score

KPI_WEIGHTS = {
    "engagement_rate": 0.4,
    "comments_quality": 0.3,
    "link_clicks": 0.2,
    "follower_growth": 0.1,
}


def _metrics(pid: str = "p1", **over: int) -> PostMetrics:
    base = dict(
        business_id="acme",
        platform_post_id=pid,
        impressions=1_000,
        likes=40,
        comments=10,
        shares=5,
        clicks=20,
        follows=5,
    )
    base.update(over)
    return PostMetrics(**base)  # type: ignore[arg-type]


def test_composite_score_blends_kpis_into_basis_points() -> None:
    # er=55/1000=.055, comments=.01, clicks=.02, follows=.005
    # 0.4*.055 + 0.3*.01 + 0.2*.02 + 0.1*.005 = 0.0295 -> 295 bps
    assert composite_score(_metrics(), KPI_WEIGHTS) == 295


def test_higher_engagement_scores_higher() -> None:
    low = composite_score(_metrics(likes=5, comments=1, shares=0), KPI_WEIGHTS)
    high = composite_score(_metrics(likes=100, comments=40, shares=20), KPI_WEIGHTS)
    assert high > low


def test_zero_impressions_scores_zero() -> None:
    assert composite_score(_metrics(impressions=0), KPI_WEIGHTS) == 0


def test_collect_metrics_fetches_scores_and_emits_event() -> None:
    source = StubMetricsSource({"p1": _metrics("p1")})
    event = collect_metrics("p1", source, KPI_WEIGHTS)
    assert event.event_name == "PostMetricsCollected"
    assert event.business_id == "acme"
    assert event.platform_post_id == "p1"
    assert event.composite_score_bps == 295
    assert event.impressions == 1_000
