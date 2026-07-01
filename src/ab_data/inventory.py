"""Data inventory for the decisions data product — classification at ingestion.

Every landed data element is classified here (architecture/08 schema). The pipeline
tags bronze with the product's classification; this module is the record + the
lookup used by quality/governance checks.
"""

from typing import Any

# One record per data element (subset of the 08_data_inventory_template schema).
DATA_INVENTORY: list[dict[str, Any]] = [
    {
        "dataElement": "decision.decision_id",
        "owningContext": "Data Platform and Intelligence",
        "entity": "Decision",
        "classification": "confidential",
        "source": "executive.decision.made",
        "retentionPolicy": "decision_retention",
        "controls": ["access_logged", "provenance_tracked"],
    },
    {
        "dataElement": "decision.agent_id",
        "owningContext": "Data Platform and Intelligence",
        "entity": "Decision",
        "classification": "confidential",
        "source": "executive.decision.made",
        "retentionPolicy": "decision_retention",
        "controls": ["access_logged", "provenance_tracked"],
    },
]

# Column -> classification, derived from the inventory (fields not listed default to internal).
_CLASSIFICATION = {
    "decision_id": "confidential",
    "agent_id": "confidential",
}


def classify(column: str) -> str:
    return _CLASSIFICATION.get(column, "internal")
