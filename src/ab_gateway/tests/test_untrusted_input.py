"""A sensitive tool fails closed under an untrusted-input flow (prompt-injection defense),
yet the same call on a trusted flow still succeeds. Runs against `make up-infra`."""

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_audit import store
from ab_common import db

ALLOWED_AGENT = "executive.cmo_agent"


def _count_decisions(decision_id: str) -> int:
    with db.connect() as conn:
        row = conn.execute("SELECT count(*) FROM decisions WHERE decision_id=%s", (decision_id,)).fetchone()
    return int(row[0]) if row else 0


def _write(client: TestClient, token: str, decision_id: str, *, untrusted: bool) -> object:
    return client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool": "decision_registry.write",
            "args": {"decision_id": decision_id, "title": "x", "authority_level": 1},
            "purpose": "record a decision",
            "untrusted_input": untrusted,
        },
    )


def test_sensitive_write_blocked_on_untrusted_flow(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(ALLOWED_AGENT)
    decision_id = f"decision_{uuid.uuid4().hex[:8]}"

    resp = _write(gateway_client, token, decision_id, untrusted=True)

    assert resp.status_code == 403
    assert resp.json()["reason"] == "sensitive tool blocked under untrusted-input flow"
    assert _count_decisions(decision_id) == 0  # the tool never ran (fail closed)
    deny = [r for r in store.read(action="decision_registry.write") if r["outcome"] == "deny"]
    assert any(r["resource"] == decision_id for r in deny)
    assert store.verify_chain() is True


def test_same_write_succeeds_on_trusted_flow(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(ALLOWED_AGENT)
    decision_id = f"decision_{uuid.uuid4().hex[:8]}"

    resp = _write(gateway_client, token, decision_id, untrusted=False)

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert _count_decisions(decision_id) == 1
