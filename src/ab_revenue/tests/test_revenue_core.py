"""Revenue rail: charges book to the ledger and publish RevenueReceived (pure, infra-free)."""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger
from ab_revenue.core import Charge, record_charges, to_event, to_transaction
from ab_revenue.gateway import StubRevenueGateway


def _charge(bid: str = "acme", amount: int = 50_000, *, ref: str = "ch_1") -> Charge:
    return Charge(
        business_id=bid,
        amount_minor=amount,
        currency="EUR",
        customer_ref="cus_1",
        external_ref=ref,
    )


def test_charge_books_balanced_revenue_to_the_ledger() -> None:
    led = InMemoryLedger()
    led.post(to_transaction(_charge(amount=50_000), maker="revenue.rail"))
    assert led.business_revenue("acme") == 50_000  # income recognised
    assert led.account_balance("acme:cash") == 50_000  # cash received
    assert led.trial_balance() == 0  # money conserved


def test_charge_becomes_a_business_scoped_event() -> None:
    ev = to_event(_charge(amount=50_000, ref="ch_9"), producer="revenue.rail")
    assert ev.event_name == "RevenueReceived"
    assert ev.business_id == "acme"
    assert ev.amount_minor == 50_000
    assert ev.external_ref == "ch_9"


def test_record_charges_books_all_and_emits_one_event_each() -> None:
    led = InMemoryLedger()
    gateway = StubRevenueGateway(
        [
            _charge("acme", 30_000, ref="a1"),
            _charge("acme", 20_000, ref="a2"),
            _charge("beta", 70_000, ref="b1"),
        ]
    )
    events = record_charges(gateway, led, maker="revenue.rail")
    assert len(events) == 3
    assert led.business_revenue("acme") == 50_000
    assert led.business_revenue("beta") == 70_000
    assert led.trial_balance() == 0


def test_record_charges_is_idempotent_on_external_ref() -> None:
    led = InMemoryLedger()
    charges = [_charge("acme", 40_000, ref="dup")]
    record_charges(StubRevenueGateway(charges), led, maker="revenue.rail")
    record_charges(StubRevenueGateway(charges), led, maker="revenue.rail")  # same charge again
    assert led.business_revenue("acme") == 40_000  # booked once
