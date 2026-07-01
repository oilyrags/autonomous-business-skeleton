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

import os

from ab_evals.gate import evaluate_and_gate
from ab_evals.registry import PromotionRegistry
from ab_evals.suites import SUITES
from ab_gateway import providers

PROMOTIONS = PromotionRegistry()
# Provider is a deployment choice (AB_MODEL_PROVIDER): the offline stub by default, or a
# real model via Portkey. Either way it must pass the eval gate below to be served.
_SERVED = providers.select_model()


def _seed_promotions() -> None:
    """At import, gate the served model against every suite; promote those it passes.

    Only auto-gate offline-evaluable models (the stub) so import never makes a network
    call; a live provider (Portkey) is promoted via an explicit eval run, or by setting
    AB_EVAL_ON_BOOT=1 to gate it at startup. Un-promoted => the gateway abstains (safe)."""
    if not (providers.is_offline(_SERVED) or os.environ.get("AB_EVAL_ON_BOOT") == "1"):
        return
    for profile, eval_set in SUITES.items():
        if evaluate_and_gate(_SERVED, eval_set).promoted:
            PROMOTIONS.promote(profile, _SERVED.version)


_seed_promotions()


def complete(task_profile: str, prompt: str) -> str:
    if not PROMOTIONS.is_promoted(task_profile):
        return f"[fallback:{task_profile}] no eval-gated model — abstain"
    return _SERVED.complete(task_profile, prompt)
