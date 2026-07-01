"""Task-profile routing table for the model gateway (architecture/11 §1).

Routing is by **task profile**, not model name: an agent declares a `taskProfile` and the
gateway maps it to a model + params. When the Portkey provider is active each route maps to
either a Portkey **config** id (which itself encodes provider/model/fallbacks/load-balancing
on Portkey's side — the idiomatic mapping) or a direct model + **virtual key**. Everything
is env-overridable so model selection is a deployment decision, not a code change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskRoute:
    """How one task profile is served when routed through Portkey."""

    # Prefer a Portkey config id (encodes model + fallbacks + load-balancing on Portkey's
    # side). If absent, use a direct model name + optional virtual key.
    config: str | None = None
    model: str | None = None
    virtual_key: str | None = None
    params: dict[str, object] = field(default_factory=dict)
    # Design's fallbackProfile: what to fall back to on gate/guardrail failure (advisory
    # here; Portkey configs also do their own fallback/retry).
    fallback_profile: str | None = None


def _route_from_env(profile: str, *, default_model: str, params: dict[str, object]) -> TaskRoute:
    """Build a route for a profile, letting env override config/model/virtual-key.

    Keys: AB_PORTKEY_CONFIG_<PROFILE>, AB_PORTKEY_MODEL_<PROFILE>, AB_PORTKEY_VK_<PROFILE>,
    AB_PORTKEY_MAX_TOKENS. A non-trivial max_tokens default matters: *reasoning* models
    (e.g. GLM-5.2) spend tokens "thinking" and return EMPTY content if the budget is too
    small — verified live, so we default generously rather than surprise the caller.
    """
    key = profile.upper()
    return TaskRoute(
        config=os.environ.get(f"AB_PORTKEY_CONFIG_{key}"),
        model=os.environ.get(f"AB_PORTKEY_MODEL_{key}", default_model),
        virtual_key=os.environ.get(f"AB_PORTKEY_VK_{key}") or os.environ.get("AB_PORTKEY_VIRTUAL_KEY"),
        params={"max_tokens": int(os.environ.get("AB_PORTKEY_MAX_TOKENS", "1024")), **params},
    )


# Task profile -> route. Defaults are conservative (small model, low temperature); a
# deployment points these at real providers via Portkey configs/virtual keys through env.
ROUTES: dict[str, TaskRoute] = {
    "executive_reasoning": _route_from_env(
        "executive_reasoning", default_model="gpt-4o-mini", params={"temperature": 0.2}
    ),
}
