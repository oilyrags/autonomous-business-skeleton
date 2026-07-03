"""The product port (PRD 0008 P3): how the console records a human approval at a DPIA/launch gate.

Approving a gate advances a governed initiative through the SDLC, so the console never mutates the
pipeline itself — it dispatches through the governed path, recording the operator as the actor
(VULN-001; the E2/GrowthPort pattern). The stub records for tests + the demo; a gateway-backed
adapter lands with the backend approval endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ProductOutcome:
    ok: bool
    detail: str


class ProductPort(Protocol):
    """Approve a pending human gate (DPIA/launch) through the governed path."""

    def approve(self, initiative_id: str, *, stage: str, actor: str, note: str = "") -> ProductOutcome: ...


@dataclass
class StubProductPort:
    """Records approvals for tests + the demo; a gateway-backed adapter implements the same port."""

    approvals: list[dict[str, str]] = field(default_factory=list)

    def approve(self, initiative_id: str, *, stage: str, actor: str, note: str = "") -> ProductOutcome:
        self.approvals.append({"initiative_id": initiative_id, "stage": stage, "actor": actor, "note": note})
        return ProductOutcome(ok=True, detail=f"approved {stage} for {initiative_id}")
