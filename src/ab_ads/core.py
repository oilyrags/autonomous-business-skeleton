"""Paid acquisition (deterministic): a business runs an ad campaign, the spend is booked to the
ledger as an outbound payment, and attributed conversions close the loop so CAC is computed from
real spend and real customers. Money is integer minor units; the external ad platform lives behind
``ab_ads.platform.AdPlatform``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

from ab_ledger.core import Posting, Transaction
from ab_schemas.events import AdSpendPlaced, DataClassification, SubjectRef


class AdCampaign(BaseModel):
    business_id: str
    spend_minor: int = Field(ge=0)
    channel: str
    external_ref: str


class AdResult(BaseModel):
    business_id: str
    channel: str
    spend_minor: int = Field(ge=0)
    conversions: int = Field(ge=0)
    external_ref: str


class LedgerPoster(Protocol):
    def post(self, txn: Transaction, cap: int = ...) -> bool: ...


class CampaignRunner(Protocol):
    def run(self, campaign: AdCampaign) -> AdResult: ...


def attributed_cac_minor(result: AdResult) -> int | None:
    """Cost per acquired customer for this campaign — None when it converted nobody."""
    return result.spend_minor // result.conversions if result.conversions else None


def to_transaction(result: AdResult, *, maker: str, checker: str) -> Transaction:
    """Book ad spend as an outbound business payment: debit ``external:ad:<channel>`` (+), credit
    ``{business_id}:cash`` (−). Outbound money → maker-checker (a distinct checker approves)."""
    return Transaction(
        txn_id=f"ad_{uuid.uuid4().hex[:12]}",
        idempotency_key=f"ad_{result.external_ref}",
        postings=(
            Posting(f"external:ad:{result.channel}", result.spend_minor),
            Posting(f"{result.business_id}:cash", -result.spend_minor),
        ),
        maker=maker,
        checker=checker,
        memo=f"ads:{result.channel}",
        business_id=result.business_id,
        payee=f"ad:{result.channel}",
    )


def to_event(result: AdResult, *, producer: str = "growth.ad_agent") -> AdSpendPlaced:
    return AdSpendPlaced(
        event_name="AdSpendPlaced",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.FINANCIAL,
        subject_ref=SubjectRef(type="Business", id=result.business_id),
        business_id=result.business_id,
        channel=result.channel,
        spend_minor=result.spend_minor,
        conversions=result.conversions,
        external_ref=result.external_ref,
    )


def run_campaigns(
    platform: CampaignRunner,
    campaigns: list[AdCampaign],
    ledger: LedgerPoster,
    *,
    maker: str = "growth.ad_agent",
    checker: str = "treasury.control_agent",
) -> list[AdSpendPlaced]:
    """Run each campaign through the platform, book its spend to the ledger, and return the events.
    Booking is idempotent on the campaign's external ref (a replayed campaign posts nothing)."""
    events: list[AdSpendPlaced] = []
    for campaign in campaigns:
        result = platform.run(campaign)
        # Ad spend is outbound to a new payee (and may exceed the cap) → the distinct checker
        # approves it (maker-checker + allow-list handled by the ledger's own rules).
        ledger.post(to_transaction(result, maker=maker, checker=checker))
        events.append(to_event(result))
    return events
