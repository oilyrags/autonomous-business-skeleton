"""Social content demo (deterministic, no infra).

    uv run python -m ab_social

The tracer-bullet loop for one brand: plan posts from the SocialProfile, generate on-brand drafts
(stub), gate them through QA, and publish the passing ones (stub) — emitting ContentPublished. Real
content-LLM / Postiz adapters slot in behind the generator + publisher ports.
"""

from __future__ import annotations

from ab_social.core import plan, publish_content, qa
from ab_social.generator import StubContentGenerator
from ab_social.profile import Pillar, PlatformConfig, PostingRules, SocialProfile
from ab_social.publisher import StubPublisher

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
)


def main() -> int:
    generator = StubContentGenerator()
    publisher = StubPublisher()
    published = 0
    for item in plan(PROFILE, count=5):
        draft = generator.write(item, PROFILE)
        verdict = qa(draft, PROFILE)
        if not verdict.passed:
            print(f"  [REJECT] {item.platform:8} {item.pillar:12} {verdict.reasons}")
            continue
        event = publish_content(draft, PROFILE, publisher)
        assert event is not None
        published += 1
        print(
            f"  [PUBLISH] {event.platform:8} {event.pillar:12} {event.format:9} -> {event.platform_post_id}"
        )
    print(f"\n  planned 5, published {published} (QA-gated, business-scoped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
