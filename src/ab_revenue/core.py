"""Revenue rail (deterministic): a customer charge becomes a balanced ledger posting + a published
event. Money is integer minor units and flows through the double-entry ledger — a charge debits the
business's cash and credits its income account, so the trial balance stays zero. Report/booking
only; the external processor lives behind ``ab_revenue.gateway.RevenueGateway``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

from ab_ledger.core import PAYMENT_CAP_MINOR, Posting, Transaction
from ab_schemas.events import DataClassification, RevenueReceived, SubjectRef


class Charge(BaseModel):
    business_id: str
    amount_minor: int = Field(ge=0)
    currency: str = "EUR"
    customer_ref: str
    external_ref: str  # the rail's charge id — the idempotency anchor


class LedgerPoster(Protocol):
    """The slice of a ledger ``record_charges`` needs — matches ``InMemoryLedger`` and the store."""

    def post(self, txn: Transaction, cap: int = ...) -> bool: ...


class ChargeSource(Protocol):
    """The slice of the revenue rail ``record_charges`` needs (see ``gateway.RevenueGateway``)."""

    def settled_charges(self) -> list[Charge]: ...


def to_transaction(charge: Charge, *, maker: str) -> Transaction:
    """Book a charge: debit ``{business_id}:cash`` (+), credit ``{business_id}:revenue`` (−)."""
    return Transaction(
        txn_id=f"rev_{uuid.uuid4().hex[:12]}",
        idempotency_key=f"rev_{charge.external_ref}",  # dedupe replays of the same charge
        postings=(
            Posting(f"{charge.business_id}:cash", charge.amount_minor),
            Posting(f"{charge.business_id}:revenue", -charge.amount_minor),
        ),
        maker=maker,
        currency=charge.currency,
        memo=f"revenue:{charge.customer_ref}",
        business_id=charge.business_id,
    )


def to_event(charge: Charge, *, producer: str = "revenue.rail") -> RevenueReceived:
    return RevenueReceived(
        event_name="RevenueReceived",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.FINANCIAL,
        subject_ref=SubjectRef(type="Charge", id=charge.external_ref),
        business_id=charge.business_id,
        external_ref=charge.external_ref,
        amount_minor=charge.amount_minor,
        currency=charge.currency,
        customer_ref=charge.customer_ref,
    )


def record_charges(
    gateway: ChargeSource, ledger: LedgerPoster, *, maker: str = "revenue.rail"
) -> list[RevenueReceived]:
    """Pull settled charges from the rail, book each to the ledger, and return the events. Booking
    is idempotent on the rail's charge id (a replayed charge posts nothing)."""
    events: list[RevenueReceived] = []
    for charge in gateway.settled_charges():
        # Inbound revenue has no external payee — the outbound payment cap/maker-checker doesn't
        # apply (money leaving is still gated on the way out). Post exempt from the cap.
        cap = max(PAYMENT_CAP_MINOR, charge.amount_minor)
        ledger.post(to_transaction(charge, maker=maker), cap)
        events.append(to_event(charge))
    return events
