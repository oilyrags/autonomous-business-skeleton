"""Warehouse freshness — is the semantic layer fresh enough to trust?

A running semantic layer can silently fall behind the bus (consumer stalled, dbt
failing). Before a decision-intelligence context acts on a KPI it needs to know how
stale the warehouse is. ``read_freshness`` reads the observed state from silver (row
count + newest event/ingest timestamps); the pure ``staleness`` helper turns that into
an age + SLA verdict — no clock in the query, so the trust decision is deterministic
and testable.

DuckDB ``TIMESTAMP`` columns are naive; we read them back as UTC-aware so callers can
compare against ``datetime.now(tz=UTC)`` without a TypeError.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from ab_data import config

# How long the warehouse may go without fresh data before it is "stale". Overridable
# per-deployment; the data service reads it at import.
DEFAULT_SLA_SECONDS: int = int(os.environ.get("AB_FRESHNESS_SLA_SECONDS", "300"))


@dataclass(frozen=True)
class Freshness:
    """Observed warehouse state, clock-free."""

    rows: int
    latest_event_at: datetime | None  # newest business event captured (occurred_at)
    latest_ingested_at: datetime | None  # when the fabric last landed data (ingested_at)


@dataclass(frozen=True)
class Staleness:
    """SLA verdict for a given freshness reading at a given moment."""

    age_seconds: float | None  # now - latest_ingested_at; None if nothing ingested yet
    within_sla: bool
    sla_seconds: int


def _as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    ts: datetime = value
    return ts.replace(tzinfo=UTC)


def read_freshness(warehouse_dir: Path = config.WAREHOUSE_DIR) -> Freshness:
    """Read row count + newest event/ingest timestamps from the built warehouse."""
    dbpath = config.duckdb_path(warehouse_dir)
    if not dbpath.exists():
        return Freshness(rows=0, latest_event_at=None, latest_ingested_at=None)
    con = duckdb.connect(str(dbpath), read_only=True)
    try:
        row = con.sql("SELECT count(*), max(occurred_at), max(ingested_at) FROM silver_decisions").fetchone()
    finally:
        con.close()
    if not row:
        return Freshness(rows=0, latest_event_at=None, latest_ingested_at=None)
    return Freshness(rows=int(row[0]), latest_event_at=_as_utc(row[1]), latest_ingested_at=_as_utc(row[2]))


def staleness(
    latest_ingested_at: datetime | None,
    now: datetime,
    sla_seconds: int = DEFAULT_SLA_SECONDS,
) -> Staleness:
    """Turn the newest-ingest time into an age + SLA verdict. Never-ingested is out of SLA."""
    if latest_ingested_at is None:
        return Staleness(age_seconds=None, within_sla=False, sla_seconds=sla_seconds)
    age = (now - latest_ingested_at).total_seconds()
    return Staleness(age_seconds=age, within_sla=age <= sla_seconds, sla_seconds=sla_seconds)


@dataclass(frozen=True)
class Readiness:
    """Whether the semantic layer is fit to serve trusted KPIs right now."""

    ready: bool
    reason: str


def readiness(f: Freshness, now: datetime, sla_seconds: int = DEFAULT_SLA_SECONDS) -> Readiness:
    """Ready only if the warehouse is built AND within the freshness SLA."""
    if f.rows == 0:
        return Readiness(ready=False, reason="warehouse not built")
    s = staleness(f.latest_ingested_at, now, sla_seconds)
    if not s.within_sla:
        age = f"{s.age_seconds:.0f}s" if s.age_seconds is not None else "unknown"
        return Readiness(ready=False, reason=f"stale: age {age} > SLA {sla_seconds}s")
    return Readiness(ready=True, reason="ok")
