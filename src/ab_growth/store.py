"""Persisted experiment proposals (PRD 0007 E1). The growth context's write path.

Mirrors `ab_factory.store`: the pure `decide`/`to_created_event` cores hold the logic, this wires
Postgres + the bus. `create` persists a proposal (idempotent on `experiment_id`) and publishes
`ExperimentCreated` on a real insert. `business_id`-scoped throughout (multi-tenancy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg.types.json import Jsonb

from ab_common import bus, db
from ab_common.config import settings
from ab_growth.experiment import to_created_event
from ab_schemas.models import ExperimentCreate


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    business_id: str
    hypothesis: str
    arm_names: list[str]
    budget_minor: int
    status: str


def create(proposal: ExperimentCreate, experiment_id: str, *, created_by: str) -> bool:
    """Persist a proposal and publish `ExperimentCreated`. Idempotent on `experiment_id`
    (a replay of the same id is a no-op). Returns True on a real insert, False on replay."""
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO experiments (experiment_id, business_id, hypothesis, arms, "
            "budget_minor, success_metrics, status, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, 'proposed', %s) "
            "ON CONFLICT (experiment_id) DO NOTHING RETURNING experiment_id",
            (
                experiment_id,
                proposal.business_id,
                proposal.hypothesis,
                Jsonb([arm.model_dump() for arm in proposal.arms]),
                proposal.budget_minor,
                Jsonb(proposal.success_metrics),
                created_by,
            ),
        )
        applied = cur.fetchone() is not None
        conn.commit()
    if applied:
        event = to_created_event(proposal, experiment_id, producer=created_by)
        bus.publish(settings.experiment_topic, key=experiment_id, value=event.model_dump_json(by_alias=True))
    return applied


def _row_to_record(row: dict[str, Any]) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id=str(row["experiment_id"]),
        business_id=str(row["business_id"]),
        hypothesis=str(row["hypothesis"]),
        arm_names=[str(a["name"]) for a in row["arms"]],
        budget_minor=int(row["budget_minor"]),
        status=str(row["status"]),
    )


def get(experiment_id: str) -> ExperimentRecord | None:
    with db.connect() as conn:
        cur = conn.execute(
            "SELECT experiment_id, business_id, hypothesis, arms, budget_minor, status "
            "FROM experiments WHERE experiment_id = %s",
            (experiment_id,),
        )
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
    return _row_to_record(dict(zip(cols, row, strict=True))) if row else None


def list_open(business_id: str | None = None) -> list[ExperimentRecord]:
    """Proposed/running experiments, optionally scoped to one business (tenant isolation)."""
    clause, params = ("WHERE business_id = %s", (business_id,)) if business_id else ("", ())
    with db.connect() as conn:
        cur = conn.execute(
            f"SELECT experiment_id, business_id, hypothesis, arms, budget_minor, status "
            f"FROM experiments {clause + (' AND' if clause else 'WHERE')} status <> 'concluded' "
            f"ORDER BY created_at DESC",
            params,
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        return [_row_to_record(dict(zip(cols, r, strict=True))) for r in cur.fetchall()]
