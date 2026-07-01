"""Observability (pure, infra-free): cost attribution + fleet overview + anomaly detection over the
ledger. A deterministic query/rollup layer — not a tracing vendor. Reads per-business revenue and
spend from the ledger (attributed by ``business_id``), turns them into unit economics, and flags
businesses that breach spend/health thresholds. Fleet overview = the whole portfolio at a glance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ab_econ.core import UnitInputs, economics
from ab_ledger.core import LedgerSpend


class LedgerView(Protocol):
    """The read slice observability needs — matches ``InMemoryLedger`` and the Postgres store."""

    def business_revenue(self, business_id: str) -> int: ...
    def business_spend(self, business_id: str) -> LedgerSpend: ...


@dataclass(frozen=True)
class BusinessSnapshot:
    business_id: str
    revenue_minor: int
    llm_spend_minor: int
    ad_spend_minor: int
    operating_profit_minor: int
    llm_cost_ratio_bps: int | None
    verdict: str


@dataclass(frozen=True)
class FleetTotals:
    businesses: int
    total_revenue_minor: int
    total_spend_minor: int  # llm + external, across the fleet
    total_operating_profit_minor: int
    unprofitable: int


class AnomalyKind(StrEnum):
    LLM_COST_HIGH = "llm_cost_high"  # inference eats too large a share of revenue
    OPERATING_LOSS = "operating_loss"  # loss worse than the tolerated floor


@dataclass(frozen=True)
class Anomaly:
    business_id: str
    kind: AnomalyKind
    detail: str


def snapshot(ledger: LedgerView, business_id: str, *, cogs_minor: int, customers: int) -> BusinessSnapshot:
    """Attribute a business's revenue + spend from the ledger and roll it into a health snapshot."""
    spend = ledger.business_spend(business_id)
    e = economics(
        UnitInputs(
            business_id=business_id,
            revenue_minor=ledger.business_revenue(business_id),
            cogs_minor=cogs_minor,
            ad_spend_minor=spend.external_spend_minor,
            llm_spend_minor=spend.llm_spend_minor,
            customers=customers,
        )
    )
    return BusinessSnapshot(
        business_id=business_id,
        revenue_minor=ledger.business_revenue(business_id),
        llm_spend_minor=spend.llm_spend_minor,
        ad_spend_minor=spend.external_spend_minor,
        operating_profit_minor=e.operating_profit_minor,
        llm_cost_ratio_bps=e.llm_cost_ratio_bps,
        verdict=e.verdict.value,
    )


def fleet_overview(ledger: LedgerView, configs: Mapping[str, tuple[int, int]]) -> list[BusinessSnapshot]:
    """Snapshot every business in the fleet. ``configs`` maps business_id → (cogs_minor, customers)."""
    return [
        snapshot(ledger, bid, cogs_minor=cogs, customers=customers)
        for bid, (cogs, customers) in configs.items()
    ]


def fleet_totals(snapshots: list[BusinessSnapshot]) -> FleetTotals:
    """Aggregate the fleet: revenue, spend, profit, and how many are unprofitable."""
    return FleetTotals(
        businesses=len(snapshots),
        total_revenue_minor=sum(s.revenue_minor for s in snapshots),
        total_spend_minor=sum(s.llm_spend_minor + s.ad_spend_minor for s in snapshots),
        total_operating_profit_minor=sum(s.operating_profit_minor for s in snapshots),
        unprofitable=sum(1 for s in snapshots if s.verdict == "unprofitable"),
    )


def detect_anomalies(
    snapshots: list[BusinessSnapshot],
    *,
    max_llm_cost_ratio_bps: int,
    operating_loss_floor_minor: int,
) -> list[Anomaly]:
    """Flag businesses breaching a threshold: LLM cost eating too much revenue, or a loss worse than
    the tolerated floor (``operating_loss_floor_minor`` is a negative number, e.g. −50_000)."""
    anomalies: list[Anomaly] = []
    for s in snapshots:
        if s.llm_cost_ratio_bps is not None and s.llm_cost_ratio_bps > max_llm_cost_ratio_bps:
            anomalies.append(
                Anomaly(
                    s.business_id,
                    AnomalyKind.LLM_COST_HIGH,
                    f"llm cost {s.llm_cost_ratio_bps}bps > {max_llm_cost_ratio_bps}bps of revenue",
                )
            )
        if s.operating_profit_minor < operating_loss_floor_minor:
            anomalies.append(
                Anomaly(
                    s.business_id,
                    AnomalyKind.OPERATING_LOSS,
                    f"operating profit {s.operating_profit_minor} < floor {operating_loss_floor_minor}",
                )
            )
    return anomalies
