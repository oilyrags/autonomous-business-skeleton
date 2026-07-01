"""Social self-optimization (pure, deterministic) — the loop that makes the brand improve. It does
NOT invent its own experiment machinery: a content variant IS an ``ab_growth`` experiment arm
(engagements = conversions), so the existing scale/pivot/kill decision drives whether a challenger
pillar wins; a SCALE bumps that pillar's weight in the ``SocialProfile`` (changing future plans), a
KILL trims it. Cross-brand winners are distilled the ``ab_playbook`` way (frequency of what works).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Action, Decision, Experiment, Variant, decide
from ab_social.metrics import PostMetrics
from ab_social.profile import Pillar, SocialProfile

SCALE_FACTOR = 1.5  # bump a winning pillar's weight
KILL_FACTOR = 0.5  # trim a losing pillar's weight


def engagements(m: PostMetrics) -> int:
    """The conversion signal for a post = likes + comments + shares."""
    return m.likes + m.comments + m.shares


def _arm(name: str, posts: list[PostMetrics], spend_minor: int) -> Variant:
    return Variant(
        name=name,
        impressions=sum(p.impressions for p in posts),
        conversions=sum(engagements(p) for p in posts),
        spend_minor=spend_minor,
    )


def build_experiment(
    business_id: str,
    *,
    incumbent: str,
    incumbent_posts: list[PostMetrics],
    challenger: str,
    challenger_posts: list[PostMetrics],
    spend_minor: int = 0,
) -> Experiment:
    """Frame two content approaches as an A/B experiment: control = incumbent, variant = challenger."""
    return Experiment(
        experiment_id=f"{business_id}-{challenger}-vs-{incumbent}",
        business_id=business_id,
        hypothesis=f"pillar '{challenger}' engages better than '{incumbent}'",
        control=_arm(incumbent, incumbent_posts, spend_minor),
        variant=_arm(challenger, challenger_posts, spend_minor),
    )


def reweight(profile: SocialProfile, pillar_name: str, *, factor: float) -> SocialProfile:
    """Scale one pillar's weight, returning a new SocialProfile (future plans shift toward it)."""
    pillars = tuple(
        Pillar(name=p.name, weight=p.weight * factor) if p.name == pillar_name else p for p in profile.pillars
    )
    return profile.model_copy(update={"pillars": pillars})


def run_optimization(
    profile: SocialProfile,
    blueprint: Blueprint,
    *,
    incumbent_pillar: str,
    challenger_pillar: str,
    incumbent_posts: list[PostMetrics],
    challenger_posts: list[PostMetrics],
    spend_minor: int = 0,
) -> tuple[Decision, SocialProfile]:
    """Decide the challenger's fate via ``ab_growth`` and reweight the profile accordingly. SCALE →
    bump the challenger pillar; KILL → trim it; PIVOT/CONTINUE → leave the profile unchanged."""
    exp = build_experiment(
        profile.business_id,
        incumbent=incumbent_pillar,
        incumbent_posts=incumbent_posts,
        challenger=challenger_pillar,
        challenger_posts=challenger_posts,
        spend_minor=spend_minor,
    )
    decision = decide(exp, blueprint)
    if decision.action is Action.SCALE:
        profile = reweight(profile, challenger_pillar, factor=SCALE_FACTOR)
    elif decision.action is Action.KILL:
        profile = reweight(profile, challenger_pillar, factor=KILL_FACTOR)
    return decision, profile


def distil_winning_pillars(
    winning_profiles: Iterable[SocialProfile], *, min_brands: int = 2
) -> tuple[str, ...]:
    """Cross-brand 'what works' (the ab_playbook way): pillars a brand leads with (its top-weight
    pillar) that recur across at least ``min_brands`` winning brands, frequency-ranked. Aggregate —
    no business_id leaves the winners."""
    tops = [max(p.pillars, key=lambda x: (x.weight, x.name)).name for p in winning_profiles if p.pillars]
    freq = Counter(tops)
    return tuple(name for name, n in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])) if n >= min_brands)
