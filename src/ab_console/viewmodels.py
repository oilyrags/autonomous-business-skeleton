"""Console view-models (pure, deterministic): aggregate the existing read-models into
presentation-ready shapes. No business logic lives in templates — this is the testable seam between
the domain and the UI. Money is formatted from integer minor units; nothing here makes a decision.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ab_econ.core import UnitEconomics
from ab_growth.experiment import Decision, Experiment
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
    trend: tuple[int, ...] = ()  # recent profit history for the sparkline (oldest first)


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
    history: Mapping[str, Sequence[int]] | None = None,
) -> FleetView:
    """Build the Fleet Dashboard view — totals + per-business rows (attention first) + alert count.
    ``history`` maps business_id → recent profit series for the row's sparkline."""
    totals: FleetTotals = fleet_totals(snapshots)
    rows = [
        FleetRow(
            business_id=s.business_id,
            verdict=s.verdict,
            operating_profit_minor=s.operating_profit_minor,
            status=_worst_status(checks, s.business_id),
            trend=tuple((history or {}).get(s.business_id, ())),
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


# --- G2: Business Detail -------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessView:
    business_id: str
    verdict: str
    revenue_minor: int
    llm_spend_minor: int
    ad_spend_minor: int
    operating_profit_minor: int
    cac_minor: int | None
    gross_margin_bps: int | None
    ltv_minor: int | None
    payback_periods: int | None
    checks: list[CheckResult]  # this business's monitor checks
    experiments: list[ExperimentRow]  # this business's experiment outcomes
    status: str  # worst monitoring status


def business_detail(
    business_id: str,
    snapshots: list[BusinessSnapshot],
    economics: Mapping[str, UnitEconomics],
    checks: list[CheckResult],
    experiments: list[ExperimentRow],
) -> BusinessView | None:
    """Assemble one business's detail view; None when the id is unknown (a calm 404)."""
    snap = next((s for s in snapshots if s.business_id == business_id), None)
    if snap is None:
        return None
    econ = economics.get(business_id)
    own_checks = [c for c in checks if c.business_id == business_id]
    return BusinessView(
        business_id=business_id,
        verdict=snap.verdict,
        revenue_minor=snap.revenue_minor,
        llm_spend_minor=snap.llm_spend_minor,
        ad_spend_minor=snap.ad_spend_minor,
        operating_profit_minor=snap.operating_profit_minor,
        cac_minor=econ.cac_minor if econ else None,
        gross_margin_bps=econ.gross_margin_bps if econ else None,
        ltv_minor=econ.ltv_minor if econ else None,
        payback_periods=econ.payback_periods if econ else None,
        checks=own_checks,
        experiments=[e for e in experiments if e.business_id == business_id],
        status=_worst_status(checks, business_id),
    )


# --- G4: Experiments ------------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperimentRow:
    experiment_id: str
    business_id: str
    hypothesis: str
    action: str  # scale | pivot | kill | continue
    reason: str
    p_value: float
    lift: float
    control_rate: float
    variant_rate: float


@dataclass(frozen=True)
class ExperimentsView:
    rows: list[ExperimentRow]
    business_id: str | None  # the active filter, if any


def experiment_row(exp: Experiment, decision: Decision) -> ExperimentRow:
    """Shape one ab_growth experiment + its decision for display."""
    return ExperimentRow(
        experiment_id=exp.experiment_id,
        business_id=exp.business_id,
        hypothesis=exp.hypothesis,
        action=decision.action.value,
        reason=decision.reason,
        p_value=decision.p_value,
        lift=decision.lift,
        control_rate=exp.control.conversion_rate,
        variant_rate=exp.variant.conversion_rate,
    )


def experiments_view(rows: list[ExperimentRow], *, business_id: str | None = None) -> ExperimentsView:
    """The experiments list, optionally filtered to one business."""
    if business_id is not None:
        rows = [r for r in rows if r.business_id == business_id]
    return ExperimentsView(rows=rows, business_id=business_id)


# --- G5: Audit & Decision Explorer ----------------------------------------------------------------


@dataclass(frozen=True)
class AuditRow:
    decision_id: str
    agent_id: str
    authority_level: int
    approval_status: str
    business_id: str | None
    occurred_at: str  # ISO timestamp, pre-formatted


@dataclass(frozen=True)
class AuditView:
    rows: list[AuditRow]
    business_id: str | None
    agent_id: str | None
    integrity_intact: bool  # the audit hash-chain state (tamper evidence)


def audit_view(
    rows: list[AuditRow],
    *,
    business_id: str | None = None,
    agent_id: str | None = None,
    integrity_intact: bool,
) -> AuditView:
    """The decision explorer: filterable rows + the hash-chain integrity indicator."""
    if business_id is not None:
        rows = [r for r in rows if r.business_id == business_id]
    if agent_id is not None:
        rows = [r for r in rows if r.agent_id == agent_id]
    return AuditView(rows=rows, business_id=business_id, agent_id=agent_id, integrity_intact=integrity_intact)


# --- G3: Kill Switch / Intervention ---------------------------------------------------------------

SCOPES: tuple[tuple[str, str], ...] = (
    ("global", "Halts EVERY agent across all businesses. The whole fleet stops acting."),
    ("agent", "Halts one agent (or one business's agents). Everything else keeps running."),
)
CONFIRM_PHRASE = "HALT"


@dataclass(frozen=True)
class InterventionView:
    kill_switch_active: bool
    current_reason: str | None
    scopes: tuple[tuple[str, str], ...]
    confirm_phrase: str
    error: str | None = None
    activated: bool = False


def intervention_view(
    *,
    kill_switch_active: bool,
    current_reason: str | None = None,
    error: str | None = None,
    activated: bool = False,
) -> InterventionView:
    """The deliberate kill-switch confirm screen: scope options with blast-radius text."""
    return InterventionView(
        kill_switch_active=kill_switch_active,
        current_reason=current_reason,
        scopes=SCOPES,
        confirm_phrase=CONFIRM_PHRASE,
        error=error,
        activated=activated,
    )


# --- v0.2: KPI sparklines (inline SVG — no chart library) -----------------------------------------


def sparkline_points(values: Sequence[int], *, width: int = 120, height: int = 28, pad: int = 2) -> str:
    """SVG polyline points for a KPI trend, normalized to the value range. Deterministic; empty
    string when there aren't two points to draw."""
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = (width - 2 * pad) / (len(values) - 1)
    points = []
    for i, v in enumerate(values):
        x = pad + i * step
        y = pad + (height - 2 * pad) * (1 - (v - lo) / span)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


# --- v0.2: Decision OS workspace (pending approvals) ----------------------------------------------


@dataclass(frozen=True)
class PendingDecision:
    decision_id: str
    kind: str  # e.g. payment | reallocation | publish
    summary: str
    amount_minor: int | None
    maker: str
    required_level: int
    business_id: str | None


@dataclass(frozen=True)
class DecisionsView:
    pending: list[PendingDecision]
    acted: str | None = None  # "approved <id>" / "rejected <id>" confirmation
    error: str | None = None


def decisions_view(
    pending: list[PendingDecision], *, acted: str | None = None, error: str | None = None
) -> DecisionsView:
    """The approval queue, highest-authority first — the human-in-the-loop workspace."""
    ordered = sorted(pending, key=lambda d: (-d.required_level, d.decision_id))
    return DecisionsView(pending=ordered, acted=acted, error=error)
