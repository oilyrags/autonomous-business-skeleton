"""Model gateway — the single ingress + determinism boundary + eval-gate enforcement.

A task profile is served ONLY by a model version that has passed its eval gate
(architecture/11 §5); the promotion registry is that serving boundary. If a profile has
no promoted model, the gateway does NOT emit a best-guess — it returns a deterministic
fallback marker so callers on governed paths abstain/escalate. Decision content is NEVER
taken from model output; the gateway uses the model only to exercise the boundary.

Real providers (vLLM / managed) slot in behind ``_SERVED`` later without changing callers,
and must pass the same gate before the registry will promote them.
"""

from __future__ import annotations

from ab_evals.gate import evaluate_and_gate
from ab_evals.models import StubModel
from ab_evals.registry import PromotionRegistry
from ab_evals.suites import SUITES

PROMOTIONS = PromotionRegistry()
_SERVED = StubModel()


def _seed_promotions() -> None:
    """At import, gate the served model against every suite; promote those it passes.
    (A model that fails is left un-promoted, so the gateway falls back for that profile.)"""
    for profile, eval_set in SUITES.items():
        if evaluate_and_gate(_SERVED, eval_set).promoted:
            PROMOTIONS.promote(profile, _SERVED.version)


_seed_promotions()


def complete(task_profile: str, prompt: str) -> str:
    if not PROMOTIONS.is_promoted(task_profile):
        return f"[fallback:{task_profile}] no eval-gated model — abstain"
    return _SERVED.complete(task_profile, prompt)
