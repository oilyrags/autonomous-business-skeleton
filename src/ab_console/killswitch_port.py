"""The intervention port: how the console activates the kill switch. The console never mutates
state itself — it posts to the EXISTING governed kill-switch service (which persists, publishes the
priority event, and is audited), so the GUI can do nothing an agent couldn't. The stub records for
tests + the demo; the HTTP adapter targets the real service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ActivationResult:
    ok: bool
    detail: str


class KillSwitchPort(Protocol):
    """Activate the kill switch through the governed path."""

    def activate(
        self, *, scope: str, target_id: str | None, reason: str, activated_by: str
    ) -> ActivationResult: ...


@dataclass
class StubKillSwitchPort:
    """Records activations for tests + the render smoke; no network."""

    activations: list[dict[str, str | None]] = field(default_factory=list)

    def activate(
        self, *, scope: str, target_id: str | None, reason: str, activated_by: str
    ) -> ActivationResult:
        self.activations.append(
            {"scope": scope, "target_id": target_id, "reason": reason, "activated_by": activated_by}
        )
        return ActivationResult(ok=True, detail=f"kill switch activated (scope={scope})")


class HttpKillSwitchPort:
    """POST /activate on the real kill-switch service (docker-compose: localhost:18002)."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or os.environ.get("AB_KILLSWITCH_URL", "http://localhost:18002")).rstrip(
            "/"
        )

    def activate(
        self, *, scope: str, target_id: str | None, reason: str, activated_by: str
    ) -> ActivationResult:
        import httpx  # lazy: only needed for a real activation

        resp = httpx.post(
            f"{self._base_url}/activate",
            json={"scope": scope, "target_id": target_id, "reason": reason, "activated_by": activated_by},
            timeout=5.0,
        )
        ok = resp.status_code == 200
        return ActivationResult(ok=ok, detail=resp.text if not ok else "kill switch activated")
