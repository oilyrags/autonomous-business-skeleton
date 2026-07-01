"""Social content demo (deterministic, no infra).

    uv run python -m ab_social

The loop for one brand: plan posts from the SocialProfile, generate on-brand drafts (stub), gate
them through QA, publish the passing ones (stub) — emitting ContentPublished — then collect metrics
(stub) and score each into a composite KPI (bps). Real content-LLM / Postiz / analytics adapters
slot in behind the generator, publisher, and metrics ports.
"""

from __future__ import annotations

from ab_social.core import plan, publish_content, qa
from ab_social.generator import StubContentGenerator
from ab_social.metrics import PostMetrics, StubMetricsSource, collect_metrics
from ab_social.profile import Pillar, PlatformConfig, PostingRules, SocialProfile
from ab_social.publisher import StubPublisher

KPI_WEIGHTS = {"engagement_rate": 0.4, "comments_quality": 0.3, "link_clicks": 0.2, "follower_growth": 0.1}
PROFILE = SocialProfile(
    business_id="rocket",
    voice="Helpful, data-driven, slightly witty.",
    pillars=(Pillar(name="Productivity", weight=0.6), Pillar(name="Insights", weight=0.4)),
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


def _stub_metrics(post_id: str, platform: str) -> PostMetrics:
    # Deterministic mock analytics: linkedin outperforms x here (drives the growth loop later).
    strong = platform == "linkedin"
    return PostMetrics(
        business_id="rocket",
        platform_post_id=post_id,
        impressions=1_000,
        likes=80 if strong else 30,
        comments=25 if strong else 6,
        shares=15 if strong else 3,
        clicks=30 if strong else 12,
        follows=10 if strong else 2,
    )


def main() -> int:
    generator, publisher = StubContentGenerator(), StubPublisher()
    published: list[tuple[str, str]] = []  # (platform_post_id, platform)
    for item in plan(PROFILE, count=5):
        draft = generator.write(item, PROFILE)
        if not qa(draft, PROFILE).passed:
            print(f"  [REJECT] {item.platform:8} {item.pillar:12}")
            continue
        event = publish_content(draft, PROFILE, publisher)
        assert event is not None
        published.append((event.platform_post_id, event.platform))
        print(
            f"  [PUBLISH] {event.platform:8} {event.pillar:12} {event.format:9} -> {event.platform_post_id}"
        )

    print(f"\n  planned 5, published {len(published)}; collecting metrics + scoring:")
    source = StubMetricsSource({pid: _stub_metrics(pid, plat) for pid, plat in published})
    for pid, _ in published:
        m = collect_metrics(pid, source, KPI_WEIGHTS)
        print(f"    {pid:18} composite score {m.composite_score_bps} bps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
