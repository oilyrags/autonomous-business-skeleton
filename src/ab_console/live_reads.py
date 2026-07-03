"""Live, in-process read providers for the console (PRD 0009 S4 / ADR-0061).

When ``AB_CONSOLE_PROVIDER=live`` the store-backed panels read real state directly from the owning
contexts (reads only — every state change still goes over the governed HTTP path). Sample data stays
the default, so infra-free dev/CI is unchanged. The obs/econ/monitor-backed panels
(fleet/snapshots/econ/checks) need a console ``LedgerView`` adapter + per-business metric configs —
a follow-up; until then they remain on sample even in live mode.
"""

from __future__ import annotations

from ab_common import db
from ab_console.viewmodels import AuditRow, ExperimentRow
from ab_growth import store as growth_store
from ab_growth.store import ExperimentRecord
from ab_product import store as product_store
from ab_product.pipeline import PipelineState


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
