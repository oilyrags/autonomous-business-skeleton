"""Slice 04 — kill-switch drill: halts within SLA, fail-closed, audit-tamper."""

import json
import time
import uuid
from collections.abc import Callable

import pytest
from confluent_kafka import Consumer, TopicPartition
from fastapi.testclient import TestClient

from ab_agent.runtime import record_decision
from ab_audit import store
from ab_common import bus, db
from ab_common.config import settings
from ab_identity.tokens import issue_token
from ab_killswitch import control, state

AGENT = "executive.cmo_agent"
SLA_SECONDS = 2.0


def _decision() -> dict[str, object]:
    return {
        "decision_id": f"decision_{uuid.uuid4().hex[:8]}",
        "title": "x",
        "authority_level": 3,
        "approval_status": "approved",
    }


def _consume_kill_event(produce: Callable[[], None], timeout: float = 20.0) -> str | None:
    bus.ensure_topic(settings.kill_topic)
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": f"test-{uuid.uuid4()}",
            "enable.auto.commit": False,
        }
    )
    meta = consumer.list_topics(settings.kill_topic, timeout=10).topics[settings.kill_topic]
    parts = []
    for pid in meta.partitions:
        tp = TopicPartition(settings.kill_topic, pid)
        _lo, hi = consumer.get_watermark_offsets(tp, timeout=10)
        tp.offset = hi
        parts.append(tp)
    consumer.assign(parts)
    produce()
    deadline = time.time() + timeout
    found = None
    while time.time() < deadline:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        found = msg.value().decode()
        break
    consumer.close()
    return found


def test_global_kill_halts_within_sla(gateway_client: TestClient, clean_db: None) -> None:
    token = issue_token(AGENT)

    event = _consume_kill_event(lambda: control.activate("global", None, "drill", "tester"))

    start = time.time()
    resp = record_decision(gateway_client, token, _decision())
    elapsed = time.time() - start

    assert resp.status_code == 403
    assert resp.json()["reason"] == "kill switch active"
    assert elapsed < SLA_SECONDS

    assert event is not None
    assert json.loads(event)["eventName"] == "KillSwitchActivated"
    assert len(store.read(action="killswitch.activate")) >= 1


def test_per_agent_kill_is_scoped(gateway_client: TestClient, clean_db: None) -> None:
    token = issue_token(AGENT)

    # Killing a different agent does not affect ours.
    control.activate("agent", "executive.intern_agent", "drill", "tester")
    assert record_decision(gateway_client, token, _decision()).status_code == 200

    # Killing ours denies it.
    control.activate("agent", AGENT, "drill", "tester")
    assert record_decision(gateway_client, token, _decision()).status_code == 403


def test_gateway_fails_closed_when_state_unreadable(
    gateway_client: TestClient, clean_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_principal: str) -> bool:
        raise RuntimeError("kill-switch store unreachable")

    monkeypatch.setattr(state, "is_killed", boom)
    token = issue_token(AGENT)
    resp = record_decision(gateway_client, token, _decision())
    assert resp.status_code == 403  # denied, not allowed


def test_tampering_breaks_the_audit_chain(gateway_client: TestClient, clean_db: None) -> None:
    token = issue_token(AGENT)
    assert record_decision(gateway_client, token, _decision()).status_code == 200
    assert store.verify_chain() is True

    with db.connect() as conn:
        conn.execute("UPDATE audit_log SET outcome='tampered' WHERE seq = (SELECT min(seq) FROM audit_log)")
        conn.commit()

    assert store.verify_chain() is False
