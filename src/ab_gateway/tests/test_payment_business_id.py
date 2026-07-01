"""A business-scoped payment attributes the money to its business: the published LedgerEntryPosted
event and the persisted ledger_txns row both carry business_id. Runs against `make up-infra`."""

import json
import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

from ab_common import bus, db
from ab_common.config import settings
from ab_factory import store as factory_store
from ab_growth.blueprint import Blueprint

AGENT = "executive.cmo_agent"
CHECKER = "controller_agent"


def _bp(business_id: str) -> Blueprint:
    return Blueprint(
        business_id=business_id,
        name=business_id.title(),
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
    )


def _persisted_business_id(txn_key: str) -> str | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT business_id FROM ledger_txns WHERE idempotency_key = %s", (txn_key,)
        ).fetchone()
    return row[0] if row else None


def test_business_scoped_payment_attributes_event_and_row(
    gateway_client: TestClient, clean_db: None, make_token: Callable[[str], str]
) -> None:
    bid = f"acme{uuid.uuid4().hex[:6]}"
    factory_store.provision(_bp(bid), capital_minor=500_000)  # funds {bid}:cash, activates
    token = make_token(AGENT)
    key = f"pay_{uuid.uuid4().hex[:8]}"
    args = {
        "idempotency_key": key,
        "amount_minor": 40_000,
        "payee": "supplier",
        "checker": CHECKER,  # distinct approver (payee not on the allow-list)
        "business_id": bid,
    }
    resp = gateway_client.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "payments.transfer", "purpose": "pay supplier for the business", "args": args},
    )
    assert resp.status_code == 200 and resp.json()["status"] == "ok"

    assert _persisted_business_id(key) == bid  # ledger row attributed to the business

    group = f"led-{uuid.uuid4().hex[:6]}"
    events = [json.loads(v) for v in bus.consume(settings.ledger_topic, group, max_messages=50, timeout=5.0)]
    mine = [e for e in events if e.get("idempotencyKey") == key]
    assert len(mine) == 1 and mine[0]["businessId"] == bid  # event attributed to the business
