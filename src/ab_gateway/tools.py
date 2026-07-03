"""Tool registry (architecture/11 §2): governed capabilities the gateway may dispatch.

Every tool carries a contract — a side-effect class and a sensitivity flag — alongside its
handler. Unregistered tools are uncallable. A tool's side-effect is deterministic code,
never model output. Sensitive tools **fail closed under untrusted-input flows** (`10`
prompt-injection defense): if the agent is acting on untrusted content, a sensitive tool is
refused even when policy would otherwise allow it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from ab_common import bus, db
from ab_common.config import settings
from ab_compliance.ropa import check as ropa_check
from ab_factory import core as factory_core
from ab_factory import store as factory_store
from ab_gateway import authz
from ab_killswitch import state as killswitch
from ab_ledger import store as ledger_store
from ab_ledger.core import LedgerError, Posting, Transaction
from ab_schemas.events import DataClassification, LedgerEntryPosted, build
from ab_schemas.models import (
    DecisionWrite,
    ExperimentCreate,
    NotifyExternal,
    PaymentTransfer,
    ProductInitiative,
)

Handler = Callable[[str, dict[str, Any]], str]


class ToolDenied(Exception):
    """A tool refused the call for a business-rule reason (mapped to an audited gateway deny)."""

    def __init__(self, reason: str, status: int = 403) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


_M = TypeVar("_M", bound=BaseModel)


def _validated(model_cls: type[_M], args: dict[str, Any], *, what: str) -> _M:
    """Validate a tool's raw args into its typed model, mapping a bad payload to an audited
    ToolDenied(400) — never an uncaught 500. The validate→deny step every governed handler repeats."""
    try:
        return model_cls.model_validate(args)
    except ValidationError as exc:
        raise ToolDenied(f"invalid {what} args: {exc.error_count()} error(s)", status=400) from exc


def _require_serves(principal: str, business_id: str) -> None:
    """Tenant-bind: the principal must serve the business, else an audited ToolDenied(403) (VULN-002,
    no cross-tenant action). The serves-business guard every business-scoped handler repeats."""
    if not authz.serves_business(principal, business_id):
        raise ToolDenied(f"'{principal}' is not authorized for business '{business_id}'", status=403)


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
    """Persist a Decision; return its id. Idempotent on decision_id.

    VULN-002/003: the agent may not write a decision scoped to a business it doesn't serve, may not
    claim an authority_level above its ceiling, and may not self-assert a human-approval status."""
    d = DecisionWrite.model_validate(args)
    if d.business_id is not None:
        _require_serves(principal, d.business_id)
    if authz.exceeds_authority(principal, d.authority_level):
        raise ToolDenied(
            f"declared authority_level {d.authority_level} exceeds '{principal}' ceiling "
            f"{authz.authority_ceiling(principal)}",
            status=403,
        )
    approval_status = authz.sanitize_approval_status(d.approval_status)  # agents never self-approve
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO decisions "
            "(decision_id, title, agent_id, authority_level, approval_status, business_id) "
            "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (decision_id) DO NOTHING",
            (d.decision_id, d.title, principal, d.authority_level, approval_status, d.business_id),
        )
        conn.commit()
    return d.decision_id


def create_experiment(principal: str, args: dict[str, Any]) -> str:
    """Create a governed experiment proposal (PRD 0007). Tenant-bound (the principal must serve the
    business), affordability-gated (the business must be launch-ready and able to afford the budget
    CAP — a read, no cash moves), then persisted + `ExperimentCreated` emitted. Returns experiment_id.
    Every business-rule refusal is a `ToolDenied` (audited gateway deny), never a 500."""
    from ab_growth import store as experiment_store

    proposal = _validated(ExperimentCreate, args, what="experiment")
    _require_serves(principal, proposal.business_id)

    business, cash = _require_ready_business(principal, proposal.business_id)
    afford = factory_core.can_spend(business, proposal.budget_minor, cash_balance=cash)
    if not afford.allowed:  # budget is a CAP checked against runway; no cash is moved
        raise ToolDenied(f"business '{proposal.business_id}' cannot afford budget: {afford.reason}")

    experiment_id = f"exp_{uuid4().hex[:12]}"
    experiment_store.create(proposal, experiment_id, created_by=principal)
    return experiment_id


def promote_initiative(principal: str, args: dict[str, Any]) -> str:
    """Promote a validated initiative into a charter-conformant product scaffold (PRD 0008). The LLM
    proposes the blueprint (a spec); classification, charter, scaffold, and the conformance gate are
    deterministic. An EXTENSION must be tenant-bound; a non-conformant scaffold is refused BEFORE any
    event is emitted. Returns the product_id."""
    from ab_product.blueprint import StubProductModel
    from ab_product.charter import BusinessCharter, charter_conformance
    from ab_product.classify import classify
    from ab_product.scaffold import scaffold, to_scaffolded_event

    initiative = _validated(ProductInitiative, args, what="initiative")

    classification = classify(initiative)  # deterministic new vs extension
    if classification.kind == "extension":  # a new business has no owner yet; an extension must bind
        _require_serves(principal, classification.business_id)

    blueprint = StubProductModel().spec(initiative, classification.business_id)  # LLM seam (P5: real)
    charter = BusinessCharter(
        business_id=classification.business_id, version=1, tokens=blueprint.design_tokens
    )
    plan = scaffold(blueprint, charter)
    report = charter_conformance(plan.artifact, charter)
    if not report.ok:  # deterministic gate — no un-conformant scaffold ships
        raise ToolDenied(f"scaffold not charter-conformant: {'; '.join(report.violations)}")

    product_id = f"prod_{classification.business_id}"
    event = to_scaffolded_event(
        plan, initiative.initiative_id, classification, product_id, producer=principal
    )
    bus.publish_event(settings.product_topic, key=product_id, event=event)
    return product_id


def _require_ready_business(principal: str, business_id: str) -> tuple[factory_core.Business, int]:
    """Tenant + readiness gate shared by every business-scoped tool: the principal must be
    authorized for the business (VULN-002 — no cross-tenant action), and the business must exist and
    be launch-ready right now (live re-check of funding, kill switch, compliance). Returns
    (business, cash_balance) or raises an audited ToolDenied."""
    _require_serves(principal, business_id)
    business = factory_store.get(business_id)
    if business is None:
        raise ToolDenied(f"unknown business '{business_id}'", status=400)
    cash = ledger_store.account_balance(f"{business_id}:cash")
    ready = factory_core.readiness(
        business,
        cash_balance=cash,
        kill_switch_clear=not killswitch.is_killed(business_id),
        compliance_clear=not ropa_check(),
    )
    if not ready.ready:
        raise ToolDenied(f"business '{business_id}' not launch-ready: {'; '.join(ready.reasons)}")
    return business, cash


def _gate_business_spend(principal: str, business_id: str, amount_minor: int) -> str:
    """Factory gate for a business-scoped payment: tenant + launch-ready (shared gate), then affords
    the amount. Returns the account to debit (its cash)."""
    business, cash = _require_ready_business(principal, business_id)
    spend = factory_core.can_spend(business, amount_minor, cash_balance=cash)
    if not spend.allowed:
        raise ToolDenied(f"business '{business_id}': {spend.reason}")
    return f"{business_id}:cash"


def complete_for_business(
    principal: str, business_id: str, task_profile: str, prompt: str, *, cost_minor: int
) -> str:
    """A business-scoped model call, gated on the business's LLM budget BEFORE any inference.

    The business must exist; its cumulative LLM spend (the ``{business_id}:llm_spend`` ledger cost
    account) plus this call's cost must stay within ``blueprint.llm_budget_minor`` — otherwise the
    call is refused (402) and no model is invoked. On success the completion runs and its cost is
    metered to the ledger (debit ``{business_id}:llm_spend`` / credit ``{business_id}:cash``), so
    the budget tightens with use. Money is conserved; the trial balance stays zero.
    """
    from ab_gateway import model_gateway
    from ab_gateway.llm_budget import LLMBudgetExceeded, gate_llm_spend

    business = factory_store.get(business_id)
    if business is None:
        raise ToolDenied(f"unknown business '{business_id}'", status=400)
    spent = ledger_store.account_balance(f"{business_id}:llm_spend")
    try:
        gate_llm_spend(
            business_id,
            cost_minor=cost_minor,
            spent_minor=spent,
            budget_minor=business.blueprint.llm_budget_minor,
        )
    except LLMBudgetExceeded as exc:
        raise ToolDenied(str(exc), status=402) from exc

    result = model_gateway.complete(task_profile, prompt)  # gate passed → run the inference

    if cost_minor > 0:  # meter the spend so the next call sees it
        txn = Transaction(
            txn_id=f"txn_{uuid4().hex[:12]}",
            idempotency_key=f"llm_{uuid4().hex}",
            postings=(
                Posting(f"{business_id}:llm_spend", cost_minor),
                Posting(f"{business_id}:cash", -cost_minor),
            ),
            maker=principal,
            memo=f"llm:{task_profile}",
            business_id=business_id,
        )
        try:
            ledger_store.post(txn)
        except LedgerError as exc:
            raise ToolDenied(f"ledger rule: {exc}") from exc
    return result


def transfer_payment(principal: str, args: dict[str, Any]) -> str:
    """Move money to an external payee via the ledger. The ledger enforces double-entry,
    the cap, maker-checker, the payee allow-list, and idempotency — rule violations surface
    as a ToolDenied (an audited gateway deny), never an uncaught error."""
    p = _validated(PaymentTransfer, args, what="payment")
    from_account = p.from_account
    if p.business_id is not None:  # business-scoped: gate through the Factory, spend its own cash
        from_account = _gate_business_spend(principal, p.business_id, p.amount_minor)
    txn = Transaction(
        txn_id=f"txn_{uuid4().hex[:12]}",
        idempotency_key=p.idempotency_key,
        postings=(Posting(f"external:{p.payee}", p.amount_minor), Posting(from_account, -p.amount_minor)),
        maker=principal,
        checker=p.checker,
        currency=p.currency,
        memo=p.memo,
        payee=p.payee,
        business_id=p.business_id,
    )
    try:
        applied = ledger_store.post(txn)  # False on idempotent replay — still "ok"
    except LedgerError as exc:
        raise ToolDenied(f"ledger rule: {exc}") from exc
    if applied:  # publish the Finance domain event once per real posting (never on a replay)
        event = build(
            LedgerEntryPosted,
            subject=("LedgerTransaction", txn.txn_id),
            producer=principal,
            data_classification=DataClassification.FINANCIAL,
            txn_id=txn.txn_id,
            idempotency_key=txn.idempotency_key,
            amount_minor=txn.magnitude,
            currency=txn.currency,
            payee=p.payee,
            maker=principal,
            checker=p.checker,
            business_id=p.business_id,
        )
        bus.publish_event(settings.ledger_topic, key=txn.txn_id, event=event)
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
    "growth.experiment.create": ToolSpec(
        name="growth.experiment.create",
        handler=create_experiment,
        side_effect="write",
        sensitive=True,  # a governed, tenant-bound proposal; fails closed on untrusted input
        description="Create a governed, tenant-isolated experiment proposal (budget-capped, audited).",
    ),
    "product.initiative.promote": ToolSpec(
        name="product.initiative.promote",
        handler=promote_initiative,
        side_effect="write",
        sensitive=True,  # governed, tenant-bound; fails closed on untrusted input
        description="Promote a validated initiative into a charter-conformant product scaffold (audited).",
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
