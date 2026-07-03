"""Persisted product initiatives (PRD 0008 P2). The gated SDLC's write path: the pure `pipeline`
core holds the transitions, this wires Postgres + the bus. `business_id`-scoped; idempotent on
`initiative_id`; every persisted transition publishes `ProductStageChanged`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ab_common import bus, db
from ab_common.config import settings
from ab_product.pipeline import PipelineState, Stage, start
from ab_schemas.events import DataClassification, ProductStageChanged, SubjectRef

_COLS = "initiative_id, business_id, title, stage, status, reason"


def _publish(state: PipelineState) -> None:
    event = ProductStageChanged(
        event_name="ProductStageChanged",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer="product.engineering_agent",
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="ProductInitiative", id=state.initiative_id),
        business_id=state.business_id,
        initiative_id=state.initiative_id,
        stage=state.stage.value,
        status=state.status,
        reason=state.reason,
    )
    bus.publish(
        settings.product_stage_topic, key=state.initiative_id, value=event.model_dump_json(by_alias=True)
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
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO product_initiatives (initiative_id, business_id, title, stage, status) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (initiative_id) DO NOTHING RETURNING initiative_id",
            (initiative_id, business_id, title, state.stage.value, state.status),
        )
        applied = cur.fetchone() is not None
        conn.commit()
    if applied:
        _publish(state)
    return state


def save(state: PipelineState) -> None:
    """Persist a transition (stage/status/reason) and publish `ProductStageChanged`."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE product_initiatives SET stage = %s, status = %s, reason = %s, updated_at = now() "
            "WHERE initiative_id = %s",
            (state.stage.value, state.status, state.reason, state.initiative_id),
        )
        conn.commit()
    _publish(state)


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
