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


def _event(agent: str, occurred_at: datetime | None = None) -> AgentDecisionMade:
    did = f"decision_{uuid.uuid4().hex[:8]}"
    return AgentDecisionMade(
        event_name="AgentDecisionMade",
        event_id=str(uuid.uuid4()),
        occurred_at=occurred_at or datetime.now(tz=UTC),
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


def test_grain_aware_kpi_and_series_over_two_days(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    day1 = datetime(2026, 6, 29, 10, 0, tzinfo=UTC)
    day2 = datetime(2026, 6, 30, 14, 0, tzinfo=UTC)
    events = [
        _event("executive.cmo_agent", day1),
        _event("executive.cmo_agent", day1),
        _event("executive.cfo_agent", day2),
    ]
    pipeline.run(events, warehouse_dir=tmp_path)
    monkeypatch.setattr(config, "duckdb_path", lambda *a, **k: tmp_path / "warehouse.duckdb")

    assert app.get_metric("active_decision_days_total")["value"] == 2

    series = app.decisions_by_day()
    assert series == [
        {"day": "2026-06-29", "decision_count": 2},
        {"day": "2026-06-30", "decision_count": 1},
    ]


def test_series_before_build_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "duckdb_path", lambda *a, **k: tmp_path / "warehouse.duckdb")
    assert app.decisions_by_day() == []


def test_ready_endpoint_503_before_build_200_after(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import Response

    monkeypatch.setattr(config, "duckdb_path", lambda *a, **k: tmp_path / "warehouse.duckdb")
    resp = Response()
    body = app.ready(resp)
    assert resp.status_code == 503 and body["ready"] is False

    pipeline.run([_event("executive.cmo_agent")], warehouse_dir=tmp_path)
    resp2 = Response()
    body2 = app.ready(resp2)
    assert resp2.status_code == 200 and body2["ready"] is True
