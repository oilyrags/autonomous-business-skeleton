"""Slice 01 — happy-path tracer, driven through the gateway seam against live infra.

Proves identity + gateway + OPA(allow) + tool + persistence + audit(hash chain) +
events all hold together. Observes via the audit store and a bus consumer.
"""

import json
import time
import uuid
from collections.abc import Callable

from confluent_kafka import Consumer, TopicPartition
from fastapi.testclient import TestClient

from ab_agent.runtime import record_decision
from ab_audit import store
from ab_audit.consumer import consume_agent_decisions
from ab_common import bus, db
from ab_common.config import settings
from ab_identity.tokens import issue_token

AGENT = "executive.cmo_agent"


def _consume_for_id(
    topic: str, decision_id: str, produce: Callable[[], None], timeout: float = 20.0
) -> str | None:
    """Position a fresh consumer at the end, run ``produce``, then return the
    matching event value (deterministic — ignores pre-existing messages)."""
    bus.ensure_topic(topic)
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": f"test-{uuid.uuid4()}",
            "enable.auto.commit": False,
        }
    )
    meta = consumer.list_topics(topic, timeout=10).topics[topic]
    parts = []
    for pid in meta.partitions:
        tp = TopicPartition(topic, pid)
        _lo, hi = consumer.get_watermark_offsets(tp, timeout=10)
        tp.offset = hi
        parts.append(tp)
    consumer.assign(parts)
    produce()
    deadline = time.time() + timeout
    found: str | None = None
    while time.time() < deadline:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        value = msg.value().decode()
        if json.loads(value).get("decisionId") == decision_id:
            found = value
            break
    consumer.close()
    return found


def test_agent_records_decision_end_to_end(gateway_client: TestClient, clean_db: None) -> None:
    decision_id = f"decision_{uuid.uuid4().hex[:8]}"
    token = issue_token(AGENT)
    decision = {
        "decision_id": decision_id,
        "title": "Increase paid acquisition for Segment A",
        "authority_level": 3,
        "approval_status": "approved",
    }

    holder: dict[str, object] = {}

    def produce() -> None:
        holder["resp"] = record_decision(gateway_client, token, decision)

    event_value = _consume_for_id(settings.decision_topic, decision_id, produce)

    # 1. The call succeeds.
    resp = holder["resp"]
    assert resp.status_code == 200  # type: ignore[attr-defined]
    body = resp.json()  # type: ignore[attr-defined]
    assert body == {"status": "ok", "decision_id": decision_id, "reason": None}

    # 2. Exactly one Decision persisted, content taken from args (determinism boundary).
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT title, authority_level, agent_id FROM decisions WHERE decision_id=%s",
            (decision_id,),
        ).fetchall()
    assert rows == [("Increase paid acquisition for Segment A", 3, AGENT)]

    # 3. Exactly one immutable allow-audit record for the call; chain verifies.
    allow = [
        r
        for r in store.read(principal=AGENT, action="decision_registry.write")
        if r["resource"] == decision_id
    ]
    assert len(allow) == 1
    assert allow[0]["outcome"] == "allow"
    assert store.verify_chain() is True

    # 4. AgentDecisionMade published with our id and the AsyncAPI envelope.
    assert event_value is not None
    event = json.loads(event_value)
    assert event["eventName"] == "AgentDecisionMade"
    assert event["subjectRef"] == {"type": "Decision", "id": decision_id}

    # 5. The audit consumer records receipt of the event.
    seen = consume_agent_decisions(
        group=f"audit-{uuid.uuid4()}", target_id=decision_id, max_messages=500, timeout=15
    )
    assert decision_id in seen
    receipts = [r for r in store.read(action="event.received") if r["resource"] == decision_id]
    assert len(receipts) >= 1
