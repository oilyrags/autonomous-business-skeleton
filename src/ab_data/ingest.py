"""Bronze ingestion: land AgentDecisionMade events as Parquet with provenance."""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import duckdb

from ab_data import config
from ab_data.contracts import BRONZE_COLUMNS
from ab_schemas.events import AgentDecisionMade


def _row(event: AgentDecisionMade, ingested_at: datetime) -> tuple[object, ...]:
    return (
        event.event_id,
        event.event_name,
        event.occurred_at,
        event.producer,
        str(event.data_classification),
        event.decision_id,
        event.agent_id,
        event.authority_level,
        str(event.approval_status),
        event.art22_significant,
        ingested_at,
    )


def write_bronze(events: Sequence[AgentDecisionMade], warehouse_dir: Path = config.WAREHOUSE_DIR) -> Path:
    """Append events as a new bronze Parquet part. Returns the part path."""
    bronze = config.bronze_dir(warehouse_dir)
    bronze.mkdir(parents=True, exist_ok=True)
    path = bronze / f"part-{uuid4().hex}.parquet"
    ingested_at = datetime.now(tz=UTC)
    cols = ", ".join(f'"{name}" {typ}' for name, typ in BRONZE_COLUMNS)
    placeholders = ", ".join("?" for _ in BRONZE_COLUMNS)
    con = duckdb.connect()
    try:
        con.execute(f"CREATE TABLE bronze ({cols})")
        con.executemany(
            f"INSERT INTO bronze VALUES ({placeholders})",
            [_row(e, ingested_at) for e in events],
        )
        con.execute(f"COPY bronze TO '{path}' (FORMAT PARQUET)")
    finally:
        con.close()
    return path


def consume_to_bronze(
    *,
    group: str,
    max_messages: int = 1000,
    timeout: float = 5.0,
    warehouse_dir: Path = config.WAREHOUSE_DIR,
) -> int:
    """Consume AgentDecisionMade from the event bus into bronze. Returns count landed."""
    from ab_common import bus
    from ab_common.config import settings

    events: list[AgentDecisionMade] = []
    for value in bus.consume(settings.decision_topic, group, max_messages=max_messages, timeout=timeout):
        payload = json.loads(value)
        if payload.get("eventName") == "AgentDecisionMade":
            events.append(AgentDecisionMade.model_validate(payload))
    if events:
        write_bronze(events, warehouse_dir)
    return len(events)
