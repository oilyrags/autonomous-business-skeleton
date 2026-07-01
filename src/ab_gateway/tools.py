"""Tool registry (architecture/11 §2): governed capabilities the gateway may dispatch.

Every tool carries a contract — a side-effect class and a sensitivity flag — alongside its
handler. Unregistered tools are uncallable. A tool's side-effect is deterministic code,
never model output. Sensitive tools **fail closed under untrusted-input flows** (`10`
prompt-injection defense): if the agent is acting on untrusted content, a sensitive tool is
refused even when policy would otherwise allow it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from ab_common import bus, db
from ab_common.config import settings
from ab_ledger import store as ledger_store
from ab_ledger.core import LedgerError, Posting, Transaction
from ab_schemas.events import DataClassification, LedgerEntryPosted, SubjectRef
from ab_schemas.models import DecisionWrite, NotifyExternal, PaymentTransfer

Handler = Callable[[str, dict[str, Any]], str]


class ToolDenied(Exception):
    """A tool refused the call for a business-rule reason (mapped to an audited gateway deny)."""

    def __init__(self, reason: str, status: int = 403) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


# Ordering of data sensitivity for the egress guard. personal/financial are the top tier.
_RANK: dict[DataClassification, int] = {
    DataClassification.PUBLIC: 0,
    DataClassification.INTERNAL: 1,
    DataClassification.CONFIDENTIAL: 2,
    DataClassification.PERSONAL: 3,
    DataClassification.FINANCIAL: 3,
}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: Handler
    side_effect: str  # "read" | "write" | "irreversible"
    sensitive: bool  # blocked under untrusted-input flows (prompt-injection defense)
    description: str
    egress: bool = False  # transmits data outside the trust boundary
    clearance: DataClassification = DataClassification.INTERNAL  # max classification it may transmit
    emits_decision: bool = False  # records a Decision -> gateway emits AgentDecisionMade


def write_decision(principal: str, args: dict[str, Any]) -> str:
    """Persist a Decision; return its id. Idempotent on decision_id."""
    d = DecisionWrite.model_validate(args)
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO decisions (decision_id, title, agent_id, authority_level, approval_status) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (decision_id) DO NOTHING",
            (d.decision_id, d.title, principal, d.authority_level, d.approval_status),
        )
        conn.commit()
    return d.decision_id


def transfer_payment(principal: str, args: dict[str, Any]) -> str:
    """Move money to an external payee via the ledger. The ledger enforces double-entry,
    the cap, maker-checker, the payee allow-list, and idempotency — rule violations surface
    as a ToolDenied (an audited gateway deny), never an uncaught error."""
    try:
        p = PaymentTransfer.model_validate(args)
    except ValidationError as exc:
        raise ToolDenied(f"invalid payment args: {exc.error_count()} error(s)", status=400) from exc
    txn = Transaction(
        txn_id=f"txn_{uuid4().hex[:12]}",
        idempotency_key=p.idempotency_key,
        postings=(Posting(f"external:{p.payee}", p.amount_minor), Posting(p.from_account, -p.amount_minor)),
        maker=principal,
        checker=p.checker,
        currency=p.currency,
        memo=p.memo,
        payee=p.payee,
    )
    try:
        applied = ledger_store.post(txn)  # False on idempotent replay — still "ok"
    except LedgerError as exc:
        raise ToolDenied(f"ledger rule: {exc}") from exc
    if applied:  # publish the Finance domain event once per real posting (never on a replay)
        event = LedgerEntryPosted(
            event_name="LedgerEntryPosted",
            event_id=uuid4().hex,
            occurred_at=datetime.now(tz=UTC),
            producer=principal,
            data_classification=DataClassification.FINANCIAL,
            subject_ref=SubjectRef(type="LedgerTransaction", id=txn.txn_id),
            txn_id=txn.txn_id,
            idempotency_key=txn.idempotency_key,
            amount_minor=txn.magnitude,
            currency=txn.currency,
            payee=p.payee,
            maker=principal,
            checker=p.checker,
        )
        bus.publish(settings.ledger_topic, key=txn.txn_id, value=event.model_dump_json(by_alias=True))
    return txn.idempotency_key


def send_notification(principal: str, args: dict[str, Any]) -> str:
    """Queue an external notification (egress). Idempotent on notification_id."""
    n = NotifyExternal.model_validate(args)
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO outbox (notification_id, principal, recipient, body) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (notification_id) DO NOTHING",
            (n.notification_id, principal, n.recipient, n.body),
        )
        conn.commit()
    return n.notification_id


REGISTRY: dict[str, ToolSpec] = {
    "decision_registry.write": ToolSpec(
        name="decision_registry.write",
        handler=write_decision,
        side_effect="write",
        sensitive=True,
        description="Persist an agent Decision to the registry.",
        emits_decision=True,
    ),
    "notify.external": ToolSpec(
        name="notify.external",
        handler=send_notification,
        side_effect="irreversible",
        sensitive=True,
        description="Send a notification outside the trust boundary.",
        egress=True,
        clearance=DataClassification.INTERNAL,
    ),
    "payments.transfer": ToolSpec(
        name="payments.transfer",
        handler=transfer_payment,
        side_effect="irreversible",
        sensitive=True,  # fails closed on an untrusted-input flow
        description="Move money to an external payee via the double-entry ledger.",
    ),
}


def get(name: str) -> ToolSpec | None:
    return REGISTRY.get(name)


def blocked_by_input_trust(spec: ToolSpec, *, untrusted_input: bool) -> bool:
    """Sensitive tools fail closed when the flow is processing untrusted input."""
    return untrusted_input and spec.sensitive


def exfiltration_blocked(spec: ToolSpec, *, data_classification: DataClassification) -> bool:
    """An egress tool may not transmit data classified above its clearance."""
    return spec.egress and _RANK[data_classification] > _RANK[spec.clearance]
