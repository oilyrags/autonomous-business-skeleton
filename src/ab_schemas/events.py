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
    business_id: str | None = None  # set when the decision is scoped to a business, else None


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
    business_id: str | None = None  # set when the payment is scoped to a business, else None


class SaleClosed(Envelope):
    """A sales opportunity reached a terminal stage (won or lost). The Sales & Revenue Ops context's
    published event; a won sale drives a customer charge into the Revenue context."""

    business_id: str
    opportunity_id: str
    stage: str  # won | lost
    amount_minor: int
    reason: str


class MvpDeployed(Envelope):
    """A business's MVP/landing page was generated from its Blueprint and deployed to a URL. The
    MVP context's published event; an experiment can now point traffic at ``url``."""

    business_id: str
    url: str
    content_hash: str


class AdSpendPlaced(Envelope):
    """A business-scoped ad campaign ran: spend was placed with an ad platform and attributed
    conversions came back. Published by the Ads context; closes the acquisition loop (spend →
    customers) so CAC is computed from real spend and real conversions."""

    business_id: str
    channel: str
    spend_minor: int
    conversions: int
    external_ref: str


class ContentPublished(Envelope):
    """A social post passed QA and was published to a platform. The Social context's published
    event; business-scoped so content is attributable and can become an experiment variant."""

    business_id: str
    platform: str
    platform_post_id: str
    format: str
    pillar: str


class PostMetricsCollected(Envelope):
    """A published post's engagement metrics were collected and scored. The Social context's
    published event; ``composite_score_bps`` is the single KPI-weighted score (basis points)."""

    business_id: str
    platform_post_id: str
    impressions: int
    composite_score_bps: int


class RevenueReceived(Envelope):
    """Money received from a customer, booked to the ledger. The Revenue context's published event;
    business-scoped so income is attributable per business in the portfolio."""

    business_id: str
    external_ref: str  # the rail's charge id (idempotency anchor)
    amount_minor: int
    currency: str
    customer_ref: str


class ExperimentCreated(Envelope):
    """A governed experiment proposal was created (PRD 0007). Emitted by the growth context when
    ``growth.experiment.create`` persists a proposal; ``business_id`` scopes it (multi-tenancy)."""

    business_id: str
    experiment_id: str
    hypothesis: str
    arm_names: list[str]
    budget_minor: int
    status: str = "proposed"


class ExperimentConcluded(Envelope):
    """The Experimentation & Growth context's decision on an experiment (scale/pivot/kill/
    continue). ``business_id`` scopes it to one business in the portfolio (multi-tenancy)."""

    business_id: str
    experiment_id: str
    action: str  # scale | pivot | kill | continue
    reason: str
    p_value: float
    control_rate: float
    variant_rate: float


class BusinessActivated(Envelope):
    """A new business passed the readiness gate and went live, funded with capital. The
    Business Factory's published event; a portfolio context integrates on ``business_id``."""

    business_id: str
    name: str
    capital_minor: int


class CapitalReallocationRecommended(Envelope):
    """The Portfolio context recommends a capital action for a business (invest_more / hold /
    starve / sunset). Advisory only — capital moves are human-in-the-loop (architecture/06)."""

    business_id: str
    action: str  # invest_more | hold | starve | sunset
    capital_delta: int  # recommended change to deployed capital (minor units)
    reason: str
