"""Live, in-process read providers for the console (PRD 0009 S4 / ADR-0061).

When ``AB_CONSOLE_PROVIDER=live`` the store-backed panels read real state directly from the owning
contexts (reads only — every state change still goes over the governed HTTP path). Sample data stays
the default, so infra-free dev/CI is unchanged. The obs/econ/monitor-backed panels
(fleet/snapshots/econ/checks) need a console ``LedgerView`` adapter + per-business metric configs —
a follow-up; until then they remain on sample even in live mode.
"""

from __future__ import annotations

from ab_common import db
from ab_console.viewmodels import AuditRow, ExperimentRow, FleetView
from ab_console.viewmodels import fleet as build_fleet
from ab_econ.core import UnitEconomics, UnitInputs, economics
from ab_factory import store as factory_store
from ab_growth import store as growth_store
from ab_growth.store import ExperimentRecord
from ab_ledger import store as ledger_store
from ab_ledger.core import LedgerSpend
from ab_monitor.check import CheckResult, CheckStatus
from ab_obs.core import BusinessSnapshot, detect_anomalies, fleet_overview
from ab_product import store as product_store
from ab_product.pipeline import PipelineState

# Fleet-overview anomaly thresholds (policy constants; mirror the sample dashboard).
_MAX_LLM_COST_RATIO_BPS = 3000  # inference eating >30% of revenue is an anomaly
_OPERATING_LOSS_FLOOR_MINOR = -50_000


def audit() -> list[AuditRow]:
    """Governed decisions from the live DB (most recent first). Tolerant of a pre-`business_id`
    `decisions` table (an un-migrated volume)."""
    with db.connect() as conn:
        has_biz = (
            conn.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'decisions' AND column_name = 'business_id'"
            ).fetchone()
            is not None
        )
        biz_col = "business_id" if has_biz else "NULL AS business_id"
        rows = conn.execute(
            f"SELECT decision_id, agent_id, authority_level, approval_status, {biz_col}, created_at "
            "FROM decisions ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return [
        AuditRow(
            decision_id=str(r[0]),
            agent_id=str(r[1]),
            authority_level=int(r[2]),
            approval_status=str(r[3]),
            business_id=(str(r[4]) if r[4] is not None else None),
            occurred_at=r[5].strftime("%Y-%m-%d %H:%M:%S"),
        )
        for r in rows
    ]


def kill_switch_state() -> tuple[bool, str | None]:
    """(active, reason) for the global kill switch, read live."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT reason FROM kill_switch WHERE active AND scope = 'global' "
            "ORDER BY activated_at DESC LIMIT 1"
        ).fetchone()
    return (row is not None, str(row[0]) if row else None)


def experiment_records() -> list[ExperimentRecord]:
    return list(growth_store.list_by_business())


def experiments() -> list[ExperimentRow]:
    """Live experiments as display rows. Per-arm stats aren't persisted on the record, so they show
    0; the action column carries the concluded decision (or 'continue' while open)."""
    return [
        ExperimentRow(
            experiment_id=r.experiment_id,
            business_id=r.business_id,
            hypothesis=r.hypothesis,
            action=(r.decision or "continue"),
            reason=f"status: {r.status}",
            p_value=0.0,
            lift=0.0,
            control_rate=0.0,
            variant_rate=0.0,
        )
        for r in growth_store.list_by_business()
    ]


def product_initiatives() -> list[PipelineState]:
    return list(product_store.list_by_business())


# --- fleet / snapshots / econ / checks (ledger-backed; the last panels to go live) ---------------
#
# cogs + customers aren't captured per business yet, so they default to 0 (the live ledger drives
# revenue + spend); the operating-profit history isn't stored, so the sparklines are empty. Panels
# are live but sparse until a per-business metric source exists — see PRD 0009 (deferred follow-up).


class _LiveLedgerView:
    """A `LedgerView` over the real ledger — per-business revenue + spend from Postgres."""

    def business_revenue(self, business_id: str) -> int:
        return ledger_store.business_revenue(business_id)

    def business_spend(self, business_id: str) -> LedgerSpend:
        return ledger_store.business_spend(business_id)


def _fleet_configs() -> dict[str, tuple[int, int]]:
    return {bid: (0, 0) for bid in factory_store.list_active()}  # (cogs, customers) — not yet tracked


def snapshots() -> list[BusinessSnapshot]:
    return fleet_overview(_LiveLedgerView(), _fleet_configs())


def _checks_from(snaps: list[BusinessSnapshot]) -> list[CheckResult]:
    return [
        CheckResult(
            f"{s.business_id}-health",
            CheckStatus.CRITICAL if s.operating_profit_minor < 0 else CheckStatus.OK,
            f"operating profit {s.operating_profit_minor}",
            business_id=s.business_id,
        )
        for s in snaps
    ]


def checks() -> list[CheckResult]:
    return _checks_from(snapshots())


def econ() -> dict[str, UnitEconomics]:
    view = _LiveLedgerView()
    out: dict[str, UnitEconomics] = {}
    for bid in factory_store.list_active():
        spend = view.business_spend(bid)
        out[bid] = economics(
            UnitInputs(
                business_id=bid,
                revenue_minor=view.business_revenue(bid),
                cogs_minor=0,
                ad_spend_minor=spend.external_spend_minor,
                llm_spend_minor=spend.llm_spend_minor,
                customers=0,
            )
        )
    return out


def fleet() -> FleetView:
    snaps = snapshots()
    return build_fleet(
        snaps,
        anomalies=detect_anomalies(
            snaps,
            max_llm_cost_ratio_bps=_MAX_LLM_COST_RATIO_BPS,
            operating_loss_floor_minor=_OPERATING_LOSS_FLOOR_MINOR,
        ),
        checks=_checks_from(snaps),
        kill_switch_active=kill_switch_state()[0],
        history={},
    )
