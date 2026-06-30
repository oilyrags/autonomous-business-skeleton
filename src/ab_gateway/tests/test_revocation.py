"""Slice 03 — a revoked agent token fails immediately (independent of expiry)."""

import uuid

from fastapi.testclient import TestClient

from ab_agent.runtime import record_decision
from ab_audit import store
from ab_common import db
from ab_identity import revocation
from ab_identity.tokens import issue_token

AGENT = "executive.cmo_agent"


def _decision(title: str = "x") -> dict[str, object]:
    return {
        "decision_id": f"decision_{uuid.uuid4().hex[:8]}",
        "title": title,
        "authority_level": 3,
        "approval_status": "approved",
    }


def test_revoked_token_fails_on_next_call(gateway_client: TestClient, clean_db: None) -> None:
    token = issue_token(AGENT)

    # Works before revocation.
    first = record_decision(gateway_client, token, _decision())
    assert first.status_code == 200

    # Revoke the principal (token unchanged, not expired).
    revocation.revoke(AGENT)

    # The very next call with the same token is rejected.
    blocked = _decision()
    resp = record_decision(gateway_client, token, blocked)
    assert resp.status_code == 403
    assert resp.json()["reason"] == "credential revoked"

    with db.connect() as conn:
        row = conn.execute(
            "SELECT count(*) FROM decisions WHERE decision_id=%s", (blocked["decision_id"],)
        ).fetchone()
    assert row is not None and row[0] == 0  # tool never ran
    assert store.verify_chain() is True


def test_other_agents_unaffected_by_a_revocation(gateway_client: TestClient, clean_db: None) -> None:
    revocation.revoke("executive.intern_agent")  # someone else

    token = issue_token(AGENT)
    resp = record_decision(gateway_client, token, _decision())
    assert resp.status_code == 200
