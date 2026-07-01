"""ab_social tracer bullet: plan -> generate -> QA -> publish, end-to-end on stubs (pure)."""

from __future__ import annotations

from ab_social.core import Draft, plan, publish_content, qa
from ab_social.generator import StubContentGenerator
from ab_social.profile import Pillar, PlatformConfig, PostingRules, SocialProfile
from ab_social.publisher import StubPublisher


def _profile() -> SocialProfile:
    return SocialProfile(
        business_id="acme",
        voice="Helpful expert.",
        pillars=(Pillar(name="Productivity", weight=0.6), Pillar(name="Insights", weight=0.4)),
        platforms=(
            PlatformConfig(name="linkedin", format_mix={"carousel": 0.7, "text_post": 0.3}),
            PlatformConfig(name="x", format_mix={"thread": 0.5, "text_post": 0.5}),
        ),
        posting_rules=PostingRules(
            forbidden=("guaranteed",),
            required_elements=("cta_or_question", "relevant_hashtags_or_keywords"),
        ),
    )


def test_plan_allocates_posts_across_pillars_by_weight() -> None:
    items = plan(_profile(), count=5)
    assert len(items) == 5
    by_pillar = {p: sum(1 for i in items if i.pillar == p) for p in ("Productivity", "Insights")}
    assert by_pillar == {"Productivity": 3, "Insights": 2}  # 0.6/0.4 of 5 → 3/2


def test_plan_picks_each_platforms_top_format_and_is_deterministic() -> None:
    a = plan(_profile(), count=4)
    b = plan(_profile(), count=4)
    assert [(i.platform, i.format) for i in a] == [(i.platform, i.format) for i in b]
    linkedin = next(i for i in a if i.platform == "linkedin")
    assert linkedin.format == "carousel"  # top share on linkedin


def test_qa_rejects_a_forbidden_term() -> None:
    draft = Draft(
        business_id="acme",
        platform="x",
        format="text_post",
        pillar="Productivity",
        body="This is guaranteed to work!",
        hashtags=("#tips",),
        has_cta=True,
    )
    result = qa(draft, _profile())
    assert result.passed is False and any("guaranteed" in r for r in result.reasons)


def test_qa_rejects_a_draft_missing_required_elements() -> None:
    draft = Draft(
        business_id="acme",
        platform="x",
        format="text_post",
        pillar="Productivity",
        body="A flat statement with no hook.",
        hashtags=(),
        has_cta=False,
    )
    result = qa(draft, _profile())
    assert result.passed is False
    assert any("cta" in r for r in result.reasons) and any("hashtag" in r for r in result.reasons)


def test_stub_generated_draft_passes_qa() -> None:
    profile = _profile()
    item = plan(profile, count=1)[0]
    draft = StubContentGenerator().write(item, profile)
    assert qa(draft, profile).passed is True


def test_publish_a_passing_draft_emits_content_published() -> None:
    profile = _profile()
    item = plan(profile, count=1)[0]
    draft = StubContentGenerator().write(item, profile)
    event = publish_content(draft, profile, StubPublisher())
    assert event is not None
    assert event.event_name == "ContentPublished"
    assert event.business_id == "acme"
    assert event.platform_post_id.startswith(draft.platform)


def test_publish_a_failing_draft_publishes_nothing() -> None:
    profile = _profile()
    bad = Draft(
        business_id="acme",
        platform="x",
        format="text_post",
        pillar="Productivity",
        body="guaranteed results",
        hashtags=(),
        has_cta=False,
    )
    assert publish_content(bad, profile, StubPublisher()) is None
