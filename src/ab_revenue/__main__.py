"""Revenue rail demo (deterministic, no infra).

    uv run python -m ab_revenue

Two businesses receive customer charges through the (stub) revenue rail; each is booked to the
ledger and recognised as income. A real Stripe/Lemon Squeezy adapter slots in behind the same port.
"""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger
from ab_revenue.core import Charge, record_charges
from ab_revenue.gateway import StubRevenueGateway

CHARGES = [
    Charge(business_id="rocket", amount_minor=120_000, customer_ref="cus_a", external_ref="ch_1"),
    Charge(business_id="rocket", amount_minor=80_000, customer_ref="cus_b", external_ref="ch_2"),
    Charge(business_id="steady", amount_minor=45_000, customer_ref="cus_c", external_ref="ch_3"),
]


def main() -> int:
    led = InMemoryLedger()
    events = record_charges(StubRevenueGateway(CHARGES), led, maker="revenue.rail")
    for e in events:
        print(f"  RevenueReceived {e.business_id:7} {e.amount_minor:+8} {e.currency} (ref {e.external_ref})")
    print()
    for bid in ("rocket", "steady"):
        cash = led.account_balance(f"{bid}:cash")
        print(f"  {bid:7} recognised revenue: {led.business_revenue(bid)} (cash {cash})")
    print(f"\ntrial balance: {led.trial_balance()} (money conserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
