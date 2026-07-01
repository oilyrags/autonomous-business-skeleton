"""Persisted provisioning: capital hits the ledger, readiness gates activation, event on the bus.
Runs against `make up-infra`."""

import json
import uuid

import pytest

from ab_common import bus, db
from ab_common.config import settings
from ab_factory import store
from ab_factory.core import Status, Underfunded
from ab_growth.blueprint import Blueprint
from ab_ledger import store as ledger


def _bp(business_id: str) -> Blueprint:
    return Blueprint(
        business_id=business_id,
        name=business_id.title(),
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
    )


def test_funded_clean_business_is_activated_and_capital_hits_the_ledger(pg: None) -> None:
    bid = f"acme{uuid.uuid4().hex[:6]}"
    b = store.provision(_bp(bid), capital_minor=500_000)

    assert b.status is Status.ACTIVE
    assert store.get(bid) is not None and store.get(bid).status is Status.ACTIVE  # type: ignore[union-attr]
    assert ledger.account_balance(f"{bid}:cash") == 500_000  # capital is real ledger money
    assert ledger.trial_balance() == 0  # invariant holds

    group = f"factory-{uuid.uuid4().hex[:6]}"
    events = [
        json.loads(v) for v in bus.consume(settings.business_topic, group, max_messages=50, timeout=5.0)
    ]
    mine = [e for e in events if e.get("businessId") == bid]
    assert (
        len(mine) == 1 and mine[0]["eventName"] == "BusinessActivated" and mine[0]["capitalMinor"] == 500_000
    )


def test_business_blocked_by_killswitch_stays_draft_with_capital_locked(pg: None) -> None:
    bid = f"blocked{uuid.uuid4().hex[:6]}"
    with db.connect() as conn:  # kill this business before provisioning
        conn.execute(
            "INSERT INTO kill_switch (scope, target_id, active, reason, activated_by) "
            "VALUES ('agent', %s, true, 'test', 'test')",
            (bid,),
        )
        conn.commit()

    b = store.provision(_bp(bid), capital_minor=500_000)

    assert b.status is Status.DRAFT  # readiness blocked → not active
    assert ledger.account_balance(f"{bid}:cash") == 500_000  # capital allocated but locked
    assert ledger.trial_balance() == 0


def test_underfunded_provision_writes_nothing(pg: None) -> None:
    bid = f"poor{uuid.uuid4().hex[:6]}"
    with pytest.raises(Underfunded):
        store.provision(_bp(bid), capital_minor=100_000)  # below experiment budget
    assert store.get(bid) is None
    assert ledger.account_balance(f"{bid}:cash") == 0
