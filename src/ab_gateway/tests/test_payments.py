"""payments.transfer end-to-end: gateway controls (OPA, untrusted-input) + ledger controls
(double-entry, cap, maker-checker, payee allow-list, idempotency) on one money-movement call.
Runs against `make up-infra`."""

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_ledger import store as ledger

AGENT = "executive.cmo_agent"


def _args(payee: str = "acme", amount: int = 50_000, **kw: object) -> dict[str, object]:
    return {"idempotency_key": f"pay_{uuid.uuid4().hex[:8]}", "amount_minor": amount, "payee": payee, **kw}


def test_approved_payment_posts_to_the_ledger(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(AGENT)
    a = _args(payee="acme", amount=40_000, checker="controller_agent")  # distinct checker approves
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "payments.transfer", "purpose": "pay supplier", "args": a},
    )
    assert resp.status_code == 200 and resp.json()["status"] == "ok"
    assert ledger.account_balance("external:acme") == 40_000
    assert ledger.trial_balance() == 0


def test_new_payee_without_checker_is_denied_by_the_ledger(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(AGENT)
    a = _args(payee="brand_new_vendor", amount=40_000)  # under cap but unapproved payee, no checker
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "payments.transfer", "purpose": "pay", "args": a},
    )
    assert resp.status_code == 403
    assert "ledger rule" in resp.json()["reason"] and "approved list" in resp.json()["reason"]
    assert ledger.trial_balance() == 0  # nothing posted


def test_over_cap_payment_without_checker_is_denied(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(AGENT)
    a = _args(payee="acme", amount=150_000)  # over cap, no checker
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "payments.transfer", "purpose": "pay", "args": a},
    )
    assert resp.status_code == 403 and "cap" in resp.json()["reason"]
    assert ledger.trial_balance() == 0


def test_payment_blocked_on_untrusted_input_flow(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(AGENT)
    a = _args(payee="acme", amount=40_000, checker="controller_agent")
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "payments.transfer", "purpose": "pay", "args": a, "untrusted_input": True},
    )
    assert resp.status_code == 403
    assert resp.json()["reason"] == "sensitive tool blocked under untrusted-input flow"
    assert ledger.trial_balance() == 0  # injection could not move money


def test_duplicate_payment_is_idempotent(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    token = make_token(AGENT)
    a = _args(payee="acme", amount=40_000, checker="controller_agent")
    body = {"tool": "payments.transfer", "purpose": "pay", "args": a}
    r1 = gateway_client.post("/tool-call", headers={"Authorization": f"Bearer {token}"}, json=body)
    r2 = gateway_client.post("/tool-call", headers={"Authorization": f"Bearer {token}"}, json=body)
    assert r1.status_code == 200 and r2.status_code == 200  # replay is a no-op success
    assert ledger.account_balance("external:acme") == 40_000  # not doubled
