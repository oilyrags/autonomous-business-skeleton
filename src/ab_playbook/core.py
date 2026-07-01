"""Living Playbooks (pure, deterministic): extract what works from winning businesses into a
versioned, reusable Blueprint template, and instantiate new businesses from it. Cross-business
learning stays **aggregate** — a playbook carries median economics + module frequencies, never a
per-business identifier — so a winning strategy transfers without leaking any one business's detail.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ab_growth.blueprint import Blueprint


@dataclass(frozen=True)
class Playbook:
    version: str
    target_revenue_minor: int  # median across winners
    experiment_budget_minor: int
    min_conversion_rate: float
    max_cac_minor: int
    recommended_modules: tuple[str, ...]  # modules used by a majority of winners
    sample_size: int  # how many winning businesses it was distilled from
    module_frequency: dict[str, int] = field(default_factory=dict)  # aggregate, no business ids


def _median_int(values: list[int]) -> int:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) // 2


def _median_float(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def extract_playbook(winners: list[Blueprint], *, version: str) -> Playbook:
    """Distil a playbook from the blueprints of winning businesses.

    Economics are the median winner; ``recommended_modules`` are those a strict majority of winners
    enabled (deterministic, frequency-ranked). Aggregate only — no business_id leaves the winners.
    """
    if not winners:
        raise ValueError("cannot extract a playbook from zero winners")
    freq = Counter(m for w in winners for m in w.enabled_modules)
    majority = len(winners) // 2 + 1
    recommended = tuple(
        m for m, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])) if freq[m] >= majority
    )
    return Playbook(
        version=version,
        target_revenue_minor=_median_int([w.target_revenue_minor for w in winners]),
        experiment_budget_minor=_median_int([w.experiment_budget_minor for w in winners]),
        min_conversion_rate=_median_float([w.min_conversion_rate for w in winners]),
        max_cac_minor=_median_int([w.max_cac_minor for w in winners]),
        recommended_modules=recommended,
        sample_size=len(winners),
        module_frequency=dict(freq),
    )


def apply_playbook(playbook: Playbook, *, business_id: str, name: str) -> Blueprint:
    """Instantiate a new business's Blueprint from a playbook — the reuse half of the loop."""
    return Blueprint(
        business_id=business_id,
        name=name,
        target_revenue_minor=playbook.target_revenue_minor,
        experiment_budget_minor=playbook.experiment_budget_minor,
        min_conversion_rate=playbook.min_conversion_rate,
        max_cac_minor=playbook.max_cac_minor,
        enabled_modules=playbook.recommended_modules,
    )
