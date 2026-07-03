"""Persisted product initiatives (PRD 0008 P2). The gated SDLC's write path: the pure `pipeline`
core holds the transitions, this wires Postgres + the bus. `business_id`-scoped; idempotent on
`initiative_id`; every persisted transition publishes `ProductStageChanged`.
"""

from __future__ import annotations

from typing import Any

from ab_common import db
from ab_common.config import settings
from ab_common.eventstore import persist_and_emit
from ab_product.pipeline import PipelineState, Stage, start
from ab_schemas.events import ProductStageChanged, build

_COLS = "initiative_id, business_id, title, stage, status, reason"


def _event(state: PipelineState) -> ProductStageChanged:
    return build(
        ProductStageChanged,
        subject=("ProductInitiative", state.initiative_id),
        producer="product.engineering_agent",
        business_id=state.business_id,
        initiative_id=state.initiative_id,
        stage=state.stage.value,
        status=state.status,
        reason=state.reason,
    )


def _to_state(row: dict[str, Any]) -> PipelineState:
    return PipelineState(
        initiative_id=str(row["initiative_id"]),
        business_id=str(row["business_id"]),
        stage=Stage(str(row["stage"])),
        status=str(row["status"]),
        reason=str(row["reason"]),
    )


def create(initiative_id: str, business_id: str, title: str) -> PipelineState:
    """Start an initiative at intake and persist it (idempotent on initiative_id); publish on a real
    insert. Returns the initial state."""
    state = start(initiative_id, business_id)
    persist_and_emit(
        "INSERT INTO product_initiatives (initiative_id, business_id, title, stage, status) "
        "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (initiative_id) DO NOTHING",
        (initiative_id, business_id, title, state.stage.value, state.status),
        topic=settings.product_stage_topic,
        key=initiative_id,
        event=lambda: _event(state),
    )
    return state


def save(state: PipelineState) -> bool:
    """Persist a transition (stage/status/reason) and publish `ProductStageChanged` — but only on a
    real change. Idempotent: the UPDATE only touches a row whose (stage, status, reason) actually
    differs, and the event is published **only on a real transition** — so a retry / replay / re-save
    of the same state does not emit a duplicate `ProductStageChanged` (which would double-count in the
    KPI gauges and the data projections), and saving an unknown initiative is a no-op. Returns True
    iff this call changed the persisted row."""
    return persist_and_emit(
        "UPDATE product_initiatives SET stage = %s, status = %s, reason = %s, updated_at = now() "
        "WHERE initiative_id = %s AND (stage, status, reason) IS DISTINCT FROM (%s, %s, %s)",
        (
            state.stage.value,
            state.status,
            state.reason,
            state.initiative_id,
            state.stage.value,
            state.status,
            state.reason,
        ),
        topic=settings.product_stage_topic,
        key=state.initiative_id,
        event=lambda: _event(state),
    )


def get(initiative_id: str) -> PipelineState | None:
    with db.connect() as conn:
        cur = conn.execute(
            f"SELECT {_COLS} FROM product_initiatives WHERE initiative_id = %s", (initiative_id,)
        )
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
    return _to_state(dict(zip(cols, row, strict=True))) if row else None


def list_by_business(business_id: str | None = None) -> list[PipelineState]:
    """All initiatives, optionally scoped to one business (tenant isolation)."""
    clause, params = ("WHERE business_id = %s", (business_id,)) if business_id else ("", ())
    with db.connect() as conn:
        cur = conn.execute(
            f"SELECT {_COLS} FROM product_initiatives {clause} ORDER BY created_at DESC", params
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        return [_to_state(dict(zip(cols, r, strict=True))) for r in cur.fetchall()]
