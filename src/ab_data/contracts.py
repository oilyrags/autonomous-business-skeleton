"""Data contracts for the decisions data product.

BRONZE_COLUMNS is the raw landing schema (a data contract the producer guarantees);
DecisionFact is the silver-layer typed row consumers depend on.
"""

from datetime import datetime

from pydantic import BaseModel

# Bronze landing columns (order matters for the Parquet writer).
BRONZE_COLUMNS: list[tuple[str, str]] = [
    ("event_id", "VARCHAR"),
    ("event_name", "VARCHAR"),
    ("occurred_at", "TIMESTAMP"),
    ("producer", "VARCHAR"),
    ("data_classification", "VARCHAR"),
    ("decision_id", "VARCHAR"),
    ("agent_id", "VARCHAR"),
    ("authority_level", "INTEGER"),
    ("approval_status", "VARCHAR"),
    ("art22_significant", "BOOLEAN"),
    ("ingested_at", "TIMESTAMP"),  # provenance: when the fabric received it
]


class DecisionFact(BaseModel):
    """Silver-layer decision fact (the consumer-facing contract)."""

    decision_id: str
    agent_id: str
    authority_level: int
    approval_status: str
    occurred_at: datetime
    data_classification: str
    ingested_at: datetime
