"""The kill-switch /activate endpoint authorizes the actor (VULN-004). Auth is checked before any
control action, so the rejection paths run infra-free."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ab_common import operator_identity
from ab_common.config import settings
from ab_killswitch.app import app

_BODY = {"scope": "global", "reason": "drill"}


def _headers(operator_id: str, role: str) -> dict[str, str]:
    return {
        "X-Operator-Id": operator_id,
        "X-Operator-Role": role,
        "X-Operator-Sig": operator_identity.sign(operator_id, role, settings.operator_auth_secret),
    }


def test_unauthenticated_activation_is_rejected() -> None:
    with TestClient(app) as c:
        assert c.post("/activate", json=_BODY).status_code == 401  # no signed identity


def test_forged_signature_is_rejected() -> None:
    bad = {"X-Operator-Id": "mallory", "X-Operator-Role": "security", "X-Operator-Sig": "deadbeef"}
    with TestClient(app) as c:
        assert c.post("/activate", json=_BODY, headers=bad).status_code == 401


def test_an_agent_role_may_not_halt_the_fleet() -> None:
    # A signed but non-operator identity (e.g. a compromised agent that somehow signed) is still 403.
    with TestClient(app) as c:
        assert (
            c.post("/activate", json=_BODY, headers=_headers("executive.cmo_agent", "agent")).status_code
            == 403
        )


def test_body_cannot_spoof_the_actor(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A valid security operator activates; the verified header id — not any body field — is the actor.
    captured: dict[str, object] = {}

    def _fake_activate(
        scope: str, target_id: str | None, reason: str, activated_by: str = "operator"
    ) -> None:
        captured.update(scope=scope, activated_by=activated_by)

    monkeypatch.setattr("ab_killswitch.app.control.activate", _fake_activate)
    with TestClient(app) as c:
        resp = c.post(
            "/activate",
            json={**_BODY, "activated_by": "mallory"},  # attacker tries to spoof the actor in the body
            headers=_headers("sec.oncall", "security"),
        )
    assert resp.status_code == 200
    assert captured["activated_by"] == "sec.oncall"  # verified identity wins; body ignored
