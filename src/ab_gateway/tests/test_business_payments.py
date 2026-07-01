"""Business-scoped payments (Half 2): a payment for a business is gated by the Factory
(launch-ready + runway) on top of the ledger's own controls. Runs against `make up-infra`."""

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_factory import store as factory
from ab_growth.blueprint import Blueprint
from ab_ledger import store as ledger

AGENT = "executive.cmo_agent"


def _active_business(capital: int = 1_000_000) -> str:
    bid = f"biz{uuid.uuid4().hex[:8]}"
    bp = Blueprint(
        business_id=bid,
        name=bid,
        target_revenue_minor=5_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
    )
    factory.provision(bp, capital_minor=capital)  # funded, clean -> active
    return bid


def _pay(client: TestClient, token: str, bid: str, amount: int, payee: str = "vendor") -> object:
    return client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool": "payments.transfer",
            "purpose": "business spend",
            "args": {
                "idempotency_key": f"pay_{uuid.uuid4().hex[:8]}",
                "amount_minor": amount,
                "payee": payee,
                "checker": "controller_agent",
                "business_id": bid,
            },
        },
    )


def test_active_business_payment_debits_its_own_cash(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    bid = _active_business(capital=1_000_000)
    resp = _pay(gateway_client, make_token(AGENT), bid, amount=40_000)
    assert resp.status_code == 200, resp.text
    assert ledger.account_balance(f"{bid}:cash") == 1_000_000 - 40_000  # spent from its own runway
    assert ledger.account_balance("external:vendor") == 40_000
    assert ledger.trial_balance() == 0


def test_kill_switched_business_payment_is_blocked(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    from ab_common import db

    bid = _active_business(capital=1_000_000)
    with db.connect() as conn:  # kill the business after it was provisioned/active
        conn.execute(
            "INSERT INTO kill_switch (scope, target_id, active, reason, activated_by) "
            "VALUES ('agent', %s, true, 'test', 'test')",
            (bid,),
        )
        conn.commit()
    resp = _pay(gateway_client, make_token(AGENT), bid, amount=40_000)
    assert resp.status_code == 403 and "not launch-ready" in resp.json()["reason"]
    assert ledger.account_balance(f"{bid}:cash") == 1_000_000  # nothing spent


def test_payment_over_runway_is_blocked(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    bid = _active_business(capital=300_000)  # runway 300_000
    resp = _pay(gateway_client, make_token(AGENT), bid, amount=400_000)  # exceeds runway
    assert resp.status_code == 403 and "insufficient runway" in resp.json()["reason"]
    assert ledger.account_balance(f"{bid}:cash") == 300_000  # nothing spent


def test_unknown_business_payment_is_denied(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    resp = _pay(gateway_client, make_token(AGENT), "no-such-business", amount=10_000)
    assert resp.status_code == 400 and "unknown business" in resp.json()["reason"]


def test_payment_without_business_id_is_unchanged(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    resp = gateway_client.post(  # no business_id -> classic path, debits shared "cash"
        "/tool-call",
        headers={"Authorization": f"Bearer {make_token(AGENT)}"},
        json={
            "tool": "payments.transfer",
            "purpose": "pay",
            "args": {
                "idempotency_key": f"pay_{uuid.uuid4().hex[:8]}",
                "amount_minor": 40_000,
                "payee": "acme",
                "checker": "controller_agent",
            },
        },
    )
    assert resp.status_code == 200 and resp.json()["status"] == "ok"
    assert ledger.account_balance("external:acme") == 40_000
