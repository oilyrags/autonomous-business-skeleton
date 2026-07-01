"""Domain-event models matching ``architecture/events.asyncapi.yaml``.

Wire format is camelCase (per the AsyncAPI envelope); Python fields are snake_case
with an alias generator bridging the two. Populate by field name or alias.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PERSONAL = "personal"
    FINANCIAL = "financial"


class ApprovalStatus(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    AUTONOMOUS_WITHIN_POLICY = "autonomous_within_policy"


class KillSwitchScope(StrEnum):
    GLOBAL = "global"
    CONTEXT = "context"
    AGENT = "agent"


class _Camel(BaseModel):
    """Base: camelCase wire aliases, populate by field name or alias."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class SubjectRef(_Camel):
    type: str
    id: str


class Envelope(_Camel):
    """Common envelope carried by every domain event."""

    event_name: str
    event_id: str
    occurred_at: datetime
    producer: str
    trace_id: str | None = None
    schema_version: str = "1.0.0"
    data_classification: DataClassification
    subject_ref: SubjectRef


class AgentDecisionMade(Envelope):
    """Emitted when an agent records a material decision (see 04 / 13)."""

    decision_id: str
    agent_id: str
    authority_level: int = Field(ge=0, le=5)
    approval_status: ApprovalStatus
    art22_significant: bool = False


class KillSwitchActivated(Envelope):
    """Priority broadcast: agents must stop initiating tool calls on receipt (see 10)."""

    scope: KillSwitchScope
    target_id: str | None = None
    reason: str
    activated_by: str
    activated_at: datetime


class ModelPromoted(Envelope):
    """A model version passed its eval gate and may serve the task profile (see 11 §5)."""

    task_profile: str
    model_version: str
    eval_score: float

    art22_significant: bool = False


class ModelEvaluationFailed(Envelope):
    """A model version failed its eval gate and is blocked from serving (see 11 §5)."""

    task_profile: str
    model_version: str
    eval_score: float
    failed_cases: list[str]
    reason: str


class LedgerEntryPosted(Envelope):
    """A payment was booked to the ledger — the Finance context's published event (see 04).

    Emitted once per applied transaction (never on an idempotent replay); consumers integrate
    downstream (analytics, reconciliation) without reading the ledger's private store."""

    txn_id: str
    idempotency_key: str
    amount_minor: int
    currency: str
    payee: str
    maker: str
    checker: str | None = None
