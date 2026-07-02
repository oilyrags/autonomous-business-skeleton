"""Console view-models (pure, deterministic): aggregate the existing read-models into
presentation-ready shapes. No business logic lives in templates — this is the testable seam between
the domain and the UI. Money is formatted from integer minor units; nothing here makes a decision.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ab_monitor.check import CheckResult, CheckStatus
from ab_obs.core import Anomaly, BusinessSnapshot, FleetTotals, fleet_totals

_STATUS_RANK = {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}


def fmt_money(minor: int, currency_symbol: str = "€") -> str:
    """Format integer minor units as human money: 1_000_000 → €10,000.00."""
    sign = "-" if minor < 0 else ""
    major, cents = divmod(abs(minor), 100)
    return f"{sign}{currency_symbol}{major:,}.{cents:02d}"


@dataclass(frozen=True)
class FleetRow:
    business_id: str
    verdict: str
    operating_profit_minor: int
    status: str  # worst monitoring status for this business (OK/WARNING/CRITICAL/UNKNOWN)


@dataclass(frozen=True)
class FleetView:
    businesses: int
    total_revenue_minor: int
    total_spend_minor: int
    total_operating_profit_minor: int
    unprofitable: int
    alert_count: int
    kill_switch_active: bool
    kill_switch_reason: str | None
    rows: list[FleetRow]


def _worst_status(checks: Iterable[CheckResult], business_id: str) -> str:
    statuses = [c.status for c in checks if c.business_id == business_id]
    worst = max(statuses, default=CheckStatus.OK)
    return worst.name


def fleet(
    snapshots: list[BusinessSnapshot],
    *,
    anomalies: list[Anomaly],
    checks: list[CheckResult],
    kill_switch_active: bool,
    kill_switch_reason: str | None = None,
) -> FleetView:
    """Build the Fleet Dashboard view — totals + per-business rows (attention first) + alert count."""
    totals: FleetTotals = fleet_totals(snapshots)
    rows = [
        FleetRow(
            business_id=s.business_id,
            verdict=s.verdict,
            operating_profit_minor=s.operating_profit_minor,
            status=_worst_status(checks, s.business_id),
        )
        for s in snapshots
    ]
    rows.sort(key=lambda r: (-_STATUS_RANK.get(r.status, 0), r.operating_profit_minor))
    alert_count = sum(1 for c in checks if c.status >= CheckStatus.WARNING)
    return FleetView(
        businesses=totals.businesses,
        total_revenue_minor=totals.total_revenue_minor,
        total_spend_minor=totals.total_spend_minor,
        total_operating_profit_minor=totals.total_operating_profit_minor,
        unprofitable=totals.unprofitable,
        alert_count=alert_count,
        kill_switch_active=kill_switch_active,
        kill_switch_reason=kill_switch_reason,
        rows=rows,
    )
