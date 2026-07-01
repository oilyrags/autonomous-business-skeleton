"""End-to-end (infra-free): events -> bronze -> dbt medallion -> canonical KPI."""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from ab_data import pipeline
from ab_schemas.events import AgentDecisionMade, ApprovalStatus, DataClassification, SubjectRef


def _event(agent: str, decision_id: str | None = None, event_id: str | None = None) -> AgentDecisionMade:
    did = decision_id or f"decision_{uuid.uuid4().hex[:8]}"
    return AgentDecisionMade(
        event_name="AgentDecisionMade",
        event_id=event_id or str(uuid.uuid4()),
        occurred_at=datetime.now(tz=UTC),
        producer=agent,
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=SubjectRef(type="Decision", id=did),
        decision_id=did,
        agent_id=agent,
        authority_level=3,
        approval_status=ApprovalStatus.APPROVED,
    )


def test_pipeline_lands_models_and_computes_canonical_kpi(tmp_path: Path) -> None:
    events = [_event("executive.cmo_agent") for _ in range(3)] + [_event("executive.cfo_agent")]
    result = pipeline.run(events, warehouse_dir=tmp_path)

    assert result.bronze_rows == 4
    assert result.metrics["decisions_recorded_total"] == 4
    assert result.metrics["deciding_agents_total"] == 2
    assert result.quality_ok


def test_silver_dedups_on_event_id(tmp_path: Path) -> None:
    fixed_event_id = str(uuid.uuid4())
    e1 = _event("executive.cmo_agent", decision_id="d1", event_id=fixed_event_id)
    e2 = _event("executive.cmo_agent", decision_id="d1", event_id=fixed_event_id)  # same event
    result = pipeline.run([e1, e2], warehouse_dir=tmp_path)

    assert result.metrics["decisions_recorded_total"] == 1
    assert result.quality_ok
