"""Infra-free tests for warehouse freshness + the pure SLA verdict."""

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ab_data import freshness, pipeline
from ab_schemas.events import AgentDecisionMade, ApprovalStatus, DataClassification, SubjectRef


def _event(occurred_at: datetime) -> AgentDecisionMade:
    did = f"decision_{uuid.uuid4().hex[:8]}"
    return AgentDecisionMade(
        event_name="AgentDecisionMade",
        event_id=str(uuid.uuid4()),
        occurred_at=occurred_at,
        producer="executive.cmo_agent",
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=SubjectRef(type="Decision", id=did),
        decision_id=did,
        agent_id="executive.cmo_agent",
        authority_level=3,
        approval_status=ApprovalStatus.APPROVED,
    )


def test_staleness_never_ingested_is_out_of_sla() -> None:
    s = freshness.staleness(None, datetime.now(tz=UTC), sla_seconds=300)
    assert s.age_seconds is None
    assert s.within_sla is False


def test_staleness_fresh_within_sla() -> None:
    ingested = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
    s = freshness.staleness(ingested, ingested + timedelta(seconds=10), sla_seconds=300)
    assert s.age_seconds == 10
    assert s.within_sla is True


def test_staleness_stale_breaches_sla() -> None:
    ingested = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
    s = freshness.staleness(ingested, ingested + timedelta(seconds=600), sla_seconds=300)
    assert s.age_seconds == 600
    assert s.within_sla is False


def test_read_freshness_before_build(tmp_path: Path) -> None:
    f = freshness.read_freshness(warehouse_dir=tmp_path)
    assert f.rows == 0
    assert f.latest_event_at is None
    assert f.latest_ingested_at is None


def test_readiness_not_built_is_not_ready() -> None:
    f = freshness.Freshness(rows=0, latest_event_at=None, latest_ingested_at=None)
    r = freshness.readiness(f, datetime.now(tz=UTC))
    assert r.ready is False
    assert "not built" in r.reason


def test_readiness_stale_is_not_ready() -> None:
    ingested = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
    f = freshness.Freshness(rows=5, latest_event_at=ingested, latest_ingested_at=ingested)
    r = freshness.readiness(f, ingested + timedelta(seconds=600), sla_seconds=300)
    assert r.ready is False
    assert "stale" in r.reason


def test_readiness_built_and_fresh_is_ready() -> None:
    ingested = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
    f = freshness.Freshness(rows=5, latest_event_at=ingested, latest_ingested_at=ingested)
    r = freshness.readiness(f, ingested + timedelta(seconds=10), sla_seconds=300)
    assert r.ready is True
    assert r.reason == "ok"


def test_read_freshness_after_build_reports_newest_event(tmp_path: Path) -> None:
    older = datetime(2026, 6, 29, 9, 0, tzinfo=UTC)
    newest = datetime(2026, 6, 30, 13, 0, tzinfo=UTC)
    pipeline.run([_event(older), _event(newest)], warehouse_dir=tmp_path)

    f = freshness.read_freshness(warehouse_dir=tmp_path)
    assert f.rows == 2
    assert f.latest_event_at == newest  # UTC-aware, equals the newest occurred_at
    assert f.latest_ingested_at is not None and f.latest_ingested_at.tzinfo is not None
