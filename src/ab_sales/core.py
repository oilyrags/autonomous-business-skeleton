"""Sales & Revenue Operations (pure, deterministic): move an opportunity through a qualification →
quote → close pipeline, and turn a won deal into a customer charge for the Revenue context. No LLM
— rule-based decisions with evidence, in the ``ab_growth``/``ab_econ`` core style. Money is integer
minor units. A won sale bridges to ``ab_revenue`` (which books it to the ledger).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ab_revenue.core import Charge
from ab_schemas.events import DataClassification, SaleClosed, SubjectRef


class Stage(StrEnum):
    WON = "won"
    LOST = "lost"


class Lead(BaseModel):
    business_id: str
    opportunity_id: str
    fit_score: int = Field(ge=0, le=100)  # how well the lead matches the ICP
    budget_minor: int = Field(ge=0)  # what the buyer can spend
    amount_minor: int = Field(ge=0)  # the quoted contract value


@dataclass(frozen=True)
class SaleResult:
    business_id: str
    opportunity_id: str
    stage: Stage
    amount_minor: int  # booked value if won, else 0
    reason: str


def run_pipeline(lead: Lead, *, min_fit_score: int, min_budget_minor: int) -> SaleResult:
    """Qualify → quote → close, deterministically. Won only when the lead fits, has budget, and the
    quote is within that budget; otherwise lost with the reason."""

    def lost(reason: str) -> SaleResult:
        return SaleResult(lead.business_id, lead.opportunity_id, Stage.LOST, 0, reason)

    if lead.fit_score < min_fit_score:
        return lost(f"unqualified: fit {lead.fit_score} < {min_fit_score}")
    if lead.budget_minor < min_budget_minor:
        return lost(f"unqualified: budget {lead.budget_minor} < {min_budget_minor}")
    if lead.amount_minor > lead.budget_minor:
        return lost(f"quote {lead.amount_minor} exceeds budget {lead.budget_minor}")
    return SaleResult(
        lead.business_id, lead.opportunity_id, Stage.WON, lead.amount_minor, "won: quote within budget"
    )


def to_charge(result: SaleResult) -> Charge | None:
    """A won sale becomes a customer charge for ``ab_revenue`` to book; a lost sale → None."""
    if result.stage is not Stage.WON:
        return None
    return Charge(
        business_id=result.business_id,
        amount_minor=result.amount_minor,
        customer_ref=result.opportunity_id,
        external_ref=f"sale_{result.opportunity_id}",
    )


def expansion_charge(result: SaleResult, *, uplift_minor: int) -> Charge | None:
    """Expansion/renewal: an upsell on a won account becomes another charge (None if not won)."""
    if result.stage is not Stage.WON or uplift_minor <= 0:
        return None
    return Charge(
        business_id=result.business_id,
        amount_minor=uplift_minor,
        customer_ref=result.opportunity_id,
        external_ref=f"expand_{result.opportunity_id}",
    )


def to_event(result: SaleResult, *, producer: str = "sales.ops_agent") -> SaleClosed:
    return SaleClosed(
        event_name="SaleClosed",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.FINANCIAL,
        subject_ref=SubjectRef(type="Business", id=result.business_id),
        business_id=result.business_id,
        opportunity_id=result.opportunity_id,
        stage=result.stage.value,
        amount_minor=result.amount_minor,
        reason=result.reason,
    )
