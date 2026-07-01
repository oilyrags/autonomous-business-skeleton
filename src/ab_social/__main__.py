"""Social content demo (deterministic, no infra).

    uv run python -m ab_social

The full self-optimizing loop for one brand: plan → generate (stub) → QA → publish (stub) →
collect metrics (stub) → score → run the winning pillar through ab_growth → reweight the
SocialProfile. Real content-LLM / Postiz / analytics adapters slot in behind the ports.
"""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_social.core import plan, publish_content, qa
from ab_social.generator import StubContentGenerator
from ab_social.metrics import PostMetrics, StubMetricsSource, composite_score
from ab_social.optimize import run_optimization
from ab_social.profile import Pillar, PlatformConfig, PostingRules, SocialProfile
from ab_social.publisher import StubPublisher

KPI_WEIGHTS = {"engagement_rate": 0.4, "comments_quality": 0.3, "link_clicks": 0.2, "follower_growth": 0.1}
PROFILE = SocialProfile(
    business_id="rocket",
    voice="Helpful, data-driven, slightly witty.",
    pillars=(Pillar(name="Productivity", weight=0.5), Pillar(name="Insights", weight=0.5)),
    platforms=(
        PlatformConfig(name="linkedin", format_mix={"carousel": 0.7, "text_post": 0.3}),
        PlatformConfig(name="x", format_mix={"thread": 0.6, "text_post": 0.4}),
    ),
    posting_rules=PostingRules(
        forbidden=("guaranteed", "get rich"),
        required_elements=("cta_or_question", "relevant_hashtags_or_keywords"),
    ),
    kpi_weights=KPI_WEIGHTS,
)
BLUEPRINT = Blueprint(
    business_id="rocket",
    name="Rocket",
    target_revenue_minor=1_000_000,
    experiment_budget_minor=1_000_000,
    min_conversion_rate=0.05,
    max_cac_minor=1_000_000,
    significance_alpha=0.05,
    min_exposure_per_arm=1_000,
)


def _stub_metrics(post_id: str, pillar: str) -> PostMetrics:
    # Deterministic mock analytics: Productivity outperforms Insights here (drives the reweight).
    strong = pillar == "Productivity"
    return PostMetrics(
        business_id="rocket",
        platform_post_id=post_id,
        impressions=1_000,
        likes=90 if strong else 30,
        comments=25 if strong else 6,
        shares=15 if strong else 3,
        clicks=30 if strong else 12,
        follows=10 if strong else 2,
    )


def main() -> int:
    generator, publisher = StubContentGenerator(), StubPublisher()
    published: list[tuple[str, str]] = []  # (platform_post_id, pillar)
    for item in plan(PROFILE, count=6):
        draft = generator.write(item, PROFILE)
        if not qa(draft, PROFILE).passed:
            continue
        event = publish_content(draft, PROFILE, publisher)
        assert event is not None
        published.append((event.platform_post_id, event.pillar))
        print(f"  [PUBLISH] {event.pillar:12} {event.format:9} -> {event.platform_post_id}")

    source = StubMetricsSource({pid: _stub_metrics(pid, pillar) for pid, pillar in published})
    by_pillar: dict[str, list[PostMetrics]] = {}
    print("\n  metrics:")
    for pid, pillar in published:
        m = source.metrics(pid)
        by_pillar.setdefault(pillar, []).append(m)
        print(f"    {pid:18} {pillar:12} {composite_score(m, KPI_WEIGHTS)} bps")

    decision, optimized = run_optimization(
        PROFILE,
        BLUEPRINT,
        incumbent_pillar="Insights",
        challenger_pillar="Productivity",
        incumbent_posts=by_pillar.get("Insights", []),
        challenger_posts=by_pillar.get("Productivity", []),
    )
    print(f"\n  ab_growth decision: {decision.action.value.upper()} ({decision.reason})")
    print("  reweighted pillars:", {p.name: round(p.weight, 3) for p in optimized.pillars})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
