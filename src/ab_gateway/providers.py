"""Model providers behind the gateway (architecture/11 §1: vendor-swappable ingress).

Two providers implement the same ``ab_evals.harness.Model`` protocol, so either can be
eval-gated and served identically:

* ``StubModel`` (from ab_evals) — deterministic, offline, the default for CI/tests.
* ``PortkeyModel`` — routes a task profile to a real model via Portkey's AI gateway
  (OpenAI-compatible). Works with Portkey cloud (``https://api.portkey.ai/v1``) or the
  self-hosted OSS gateway (``AB_PORTKEY_BASE_URL=http://host:8787/v1``).

Provider choice is a deployment decision (``AB_MODEL_PROVIDER``); a Portkey model must still
pass the eval gate before the gateway will serve it, so selecting Portkey never bypasses
governance. The Portkey client is imported lazily and can be injected, so nothing here needs
network or the ``portkey-ai`` package unless a real Portkey call is actually made.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

from ab_evals.harness import Model
from ab_evals.models import StubModel
from ab_gateway.model_routes import ROUTES, TaskRoute

PORTKEY_DEFAULT_BASE_URL = "https://api.portkey.ai/v1"


class UnroutedProfileError(Exception):
    """No Portkey route is configured for this task profile."""


class ChatClient(Protocol):
    """The slice of the OpenAI-compatible client we use (Portkey SDK matches this)."""

    chat: Any


class PortkeyModel:
    """A candidate model served through Portkey. ``complete`` maps the task profile to its
    route and does one chat completion, returning the text (never used for a decision)."""

    def __init__(
        self,
        routes: dict[str, TaskRoute] | None = None,
        *,
        client: ChatClient | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        version: str = "portkey",
    ) -> None:
        self._routes = routes if routes is not None else ROUTES
        self._client = client  # injected in tests; built lazily otherwise
        self._base_url = base_url or os.environ.get("AB_PORTKEY_BASE_URL", PORTKEY_DEFAULT_BASE_URL)
        self._api_key = api_key or os.environ.get("AB_PORTKEY_API_KEY")
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def complete(self, task_profile: str, prompt: str) -> str:
        route = self._routes.get(task_profile)
        if route is None:
            raise UnroutedProfileError(task_profile)
        client = self._client or self._build_client(route)
        kwargs: dict[str, Any] = {"messages": [{"role": "user", "content": prompt}], **route.params}
        if route.model:
            kwargs["model"] = route.model
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def _build_client(self, route: TaskRoute) -> ChatClient:
        try:
            from portkey_ai import Portkey  # lazy: only needed for a real call
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError(
                "portkey-ai is not installed; `uv sync --group models` to use AB_MODEL_PROVIDER=portkey"
            ) from exc
        if not self._api_key:
            raise RuntimeError("AB_PORTKEY_API_KEY is required for the Portkey provider")
        opts: dict[str, Any] = {"api_key": self._api_key, "base_url": self._base_url}
        if route.config:
            opts["config"] = route.config
        if route.virtual_key:
            opts["virtual_key"] = route.virtual_key
        # Typed local so mypy is consistent whether or not portkey-ai is installed
        # (CI has no `models` group -> Portkey is Any; installed -> real type; both fine here).
        client: ChatClient = Portkey(**opts)
        return client


def select_model() -> Model:
    """Pick the served model from the environment. Defaults to the offline stub."""
    provider = os.environ.get("AB_MODEL_PROVIDER", "stub").lower()
    if provider == "portkey":
        return PortkeyModel()
    return StubModel()


def is_offline(model: Model) -> bool:
    """True if the model can be eval-gated at import with no network (the stub)."""
    return isinstance(model, StubModel)
