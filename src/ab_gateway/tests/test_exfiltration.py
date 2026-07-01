"""Exfiltration guard: an egress tool may not transmit data above its clearance, yet an
in-clearance send still succeeds. Runs against `make up-infra`."""

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_audit import store
from ab_common import db

ALLOWED_AGENT = "executive.cmo_agent"


def _count_outbox(notification_id: str) -> int:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT count(*) FROM outbox WHERE notification_id=%s", (notification_id,)
        ).fetchone()
    return int(row[0]) if row else 0


def _notify(client: TestClient, token: str, nid: str, classification: str) -> object:
    return client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool": "notify.external",
            "args": {"notification_id": nid, "recipient": "ops@example.com", "body": "status update"},
            "purpose": "notify ops",
            "data_classification": classification,
        },
    )


def test_personal_data_blocked_from_egress(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(ALLOWED_AGENT)
    nid = f"notif_{uuid.uuid4().hex[:8]}"

    resp = _notify(gateway_client, token, nid, "personal")

    assert resp.status_code == 403
    assert "exceeds egress clearance" in resp.json()["reason"]
    assert _count_outbox(nid) == 0  # nothing left the boundary (fail closed)
    deny = [r for r in store.read(action="notify.external") if r["outcome"] == "deny"]
    assert any(r["resource"] == nid for r in deny)
    assert store.verify_chain() is True


def test_internal_data_egress_succeeds(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(ALLOWED_AGENT)
    nid = f"notif_{uuid.uuid4().hex[:8]}"

    resp = _notify(gateway_client, token, nid, "internal")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert _count_outbox(nid) == 1
