"""Slice 02 — unauthorized calls are denied (default-deny) and audited."""

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_agent.runtime import record_decision
from ab_audit import store
from ab_common import db

ALLOWED_AGENT = "executive.cmo_agent"


def _count_decisions(decision_id: str) -> int:
    with db.connect() as conn:
        row = conn.execute("SELECT count(*) FROM decisions WHERE decision_id=%s", (decision_id,)).fetchone()
    return int(row[0]) if row else 0


def test_unapproved_tool_is_denied(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(ALLOWED_AGENT)
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "database.delete", "args": {"table": "customers"}, "purpose": "wipe data"},
    )
    assert resp.status_code == 403
    assert resp.json()["status"] == "denied"
    assert resp.json()["reason"] == "not authorized by policy"

    # No side effect; the denial is audited; chain intact.
    deny = [r for r in store.read(action="database.delete") if r["outcome"] == "deny"]
    assert len(deny) == 1
    assert store.verify_chain() is True


def test_unapproved_principal_is_denied(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    decision_id = f"decision_{uuid.uuid4().hex[:8]}"
    token = make_token("executive.intern_agent")  # not granted by policy
    decision = {"decision_id": decision_id, "title": "x", "authority_level": 1, "approval_status": "pending"}

    resp = record_decision(gateway_client, token, decision)

    assert resp.status_code == 403
    assert resp.json()["reason"] == "not authorized by policy"
    assert _count_decisions(decision_id) == 0  # the tool never ran
    assert store.verify_chain() is True
