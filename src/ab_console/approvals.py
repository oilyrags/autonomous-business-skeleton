"""The approval port: how the console acts on a pending high-stakes decision. Approve/reject is a
governed action — the real adapter dispatches through the gateway's maker-checker path (it lands
when the backend approval queue does; the ledger's checker model is per-transaction today), and
every action carries the actor + note so the governed side audits it. The stub records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ApprovalOutcome:
    ok: bool
    detail: str


class ApprovalPort(Protocol):
    """Act on a pending decision through the governed path."""

    def approve(self, decision_id: str, *, actor: str, note: str) -> ApprovalOutcome: ...
    def reject(self, decision_id: str, *, actor: str, note: str) -> ApprovalOutcome: ...


@dataclass
class StubApprovalPort:
    """Records actions for tests + the demo; a gateway-backed adapter implements the same port."""

    actions: list[dict[str, str]] = field(default_factory=list)

    def approve(self, decision_id: str, *, actor: str, note: str) -> ApprovalOutcome:
        self.actions.append({"action": "approve", "decision_id": decision_id, "actor": actor, "note": note})
        return ApprovalOutcome(ok=True, detail=f"approved {decision_id}")

    def reject(self, decision_id: str, *, actor: str, note: str) -> ApprovalOutcome:
        self.actions.append({"action": "reject", "decision_id": decision_id, "actor": actor, "note": note})
        return ApprovalOutcome(ok=True, detail=f"rejected {decision_id}")
