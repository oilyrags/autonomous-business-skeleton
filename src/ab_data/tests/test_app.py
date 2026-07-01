"""Infra-free tests for the data service HTTP layer.

We call the route functions directly (no TestClient, so no background consumer
thread and no event bus) — the endpoints read the warehouse we build in a tmp dir.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ab_data import app, config, pipeline
from ab_schemas.events import AgentDecisionMade, ApprovalStatus, DataClassification, SubjectRef


def _event(agent: str) -> AgentDecisionMade:
    did = f"decision_{uuid.uuid4().hex[:8]}"
    return AgentDecisionMade(
        event_name="AgentDecisionMade",
        event_id=str(uuid.uuid4()),
        occurred_at=datetime.now(tz=UTC),
        producer=agent,
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=SubjectRef(type="Decision", id=did),
        decision_id=did,
        agent_id=agent,
        authority_level=3,
        approval_status=ApprovalStatus.APPROVED,
    )


def test_list_metrics_exposes_canonical_registry() -> None:
    names = {m["name"] for m in app.list_metrics()}
    assert {"decisions_recorded_total", "deciding_agents_total"} <= names
    for m in app.list_metrics():
        assert m["description"] and m["grain"]


def test_get_metric_unknown_is_404() -> None:
    with pytest.raises(app.HTTPException) as exc:
        app.get_metric("not_a_real_metric")
    assert exc.value.status_code == 404


def test_get_metric_before_warehouse_built(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # duckdb_path()'s default arg is bound at import, so redirect the function itself.
    monkeypatch.setattr(config, "duckdb_path", lambda *a, **k: tmp_path / "warehouse.duckdb")
    result = app.get_metric("decisions_recorded_total")
    assert result["value"] is None
    assert "not built" in result["note"]


def test_get_metric_serves_value_after_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = [_event("executive.cmo_agent"), _event("executive.cmo_agent"), _event("executive.cfo_agent")]
    built = pipeline.run(events, warehouse_dir=tmp_path)
    assert built.metrics["decisions_recorded_total"] == 3  # sanity: warehouse built in tmp_path
    monkeypatch.setattr(config, "duckdb_path", lambda *a, **k: tmp_path / "warehouse.duckdb")

    assert app.get_metric("decisions_recorded_total")["value"] == 3
    assert app.get_metric("deciding_agents_total")["value"] == 2
