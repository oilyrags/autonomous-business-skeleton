"""Persisted experiment proposals (PRD 0007 E1). The growth context's write path.

Mirrors `ab_factory.store`: the pure `decide`/`to_created_event` cores hold the logic, this wires
Postgres + the bus. `create` persists a proposal (idempotent on `experiment_id`) and publishes
`ExperimentCreated` on a real insert. `business_id`-scoped throughout (multi-tenancy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg.types.json import Jsonb

from ab_common import db
from ab_common.config import settings
from ab_common.eventstore import persist_and_emit
from ab_growth.experiment import Decision, Experiment, to_created_event, to_event
from ab_schemas.models import ExperimentCreate


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    business_id: str
    hypothesis: str
    arm_names: list[str]
    budget_minor: int
    status: str
    decision: str | None = None  # scale|pivot|kill|continue once concluded, else None


def create(proposal: ExperimentCreate, experiment_id: str, *, created_by: str) -> bool:
    """Persist a proposal and publish `ExperimentCreated`. Idempotent on `experiment_id`
    (a replay of the same id is a no-op). Returns True on a real insert, False on replay."""
    return persist_and_emit(
        "INSERT INTO experiments (experiment_id, business_id, hypothesis, arms, "
        "budget_minor, success_metrics, status, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, 'proposed', %s) "
        "ON CONFLICT (experiment_id) DO NOTHING",
        (
            experiment_id,
            proposal.business_id,
            proposal.hypothesis,
            Jsonb([arm.model_dump() for arm in proposal.arms]),
            proposal.budget_minor,
            Jsonb(proposal.success_metrics),
            created_by,
        ),
        topic=settings.experiment_topic,
        key=experiment_id,
        event=lambda: to_created_event(proposal, experiment_id, producer=created_by),
    )


def conclude(exp: Experiment, decision: Decision) -> bool:
    """Record the outcome (status → concluded) and publish `ExperimentConcluded` — which the
    portfolio context folds into capital signals (PRD 0007 E3).

    Idempotent: the UPDATE only transitions an experiment that is not already concluded, and the
    event is published **only on a real transition** — so a retry / replay / re-run does not emit a
    duplicate `ExperimentConcluded` (which would double-count the outcome in the portfolio rollup),
    and concluding an unknown experiment is a no-op. Returns True iff this call concluded it."""
    return persist_and_emit(
        "UPDATE experiments SET status = 'concluded', decision = %s "
        "WHERE experiment_id = %s AND status <> 'concluded'",
        (decision.action.value, exp.experiment_id),
        topic=settings.experiment_concluded_topic,
        key=exp.experiment_id,
        event=lambda: to_event(exp, decision),
    )


_COLS = "experiment_id, business_id, hypothesis, arms, budget_minor, status, decision"


def _row_to_record(row: dict[str, Any]) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id=str(row["experiment_id"]),
        business_id=str(row["business_id"]),
        hypothesis=str(row["hypothesis"]),
        arm_names=[str(a["name"]) for a in row["arms"]],
        budget_minor=int(row["budget_minor"]),
        status=str(row["status"]),
        decision=str(row["decision"]) if row["decision"] is not None else None,
    )


def get(experiment_id: str) -> ExperimentRecord | None:
    with db.connect() as conn:
        cur = conn.execute(f"SELECT {_COLS} FROM experiments WHERE experiment_id = %s", (experiment_id,))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
    return _row_to_record(dict(zip(cols, row, strict=True))) if row else None


def list_open(business_id: str | None = None) -> list[ExperimentRecord]:
    """Proposed/running experiments, optionally scoped to one business (tenant isolation)."""
    clause, params = ("WHERE business_id = %s", (business_id,)) if business_id else ("", ())
    with db.connect() as conn:
        cur = conn.execute(
            f"SELECT {_COLS} FROM experiments "
            f"{clause + (' AND' if clause else 'WHERE')} status <> 'concluded' ORDER BY created_at DESC",
            params,
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        return [_row_to_record(dict(zip(cols, r, strict=True))) for r in cur.fetchall()]


def list_by_business(business_id: str | None = None) -> list[ExperimentRecord]:
    """All experiments (any status), optionally scoped to one business — feeds the KPI projection."""
    clause, params = ("WHERE business_id = %s", (business_id,)) if business_id else ("", ())
    with db.connect() as conn:
        cur = conn.execute(f"SELECT {_COLS} FROM experiments {clause} ORDER BY created_at DESC", params)
        cols = [d[0] for d in cur.description] if cur.description else []
        return [_row_to_record(dict(zip(cols, r, strict=True))) for r in cur.fetchall()]
