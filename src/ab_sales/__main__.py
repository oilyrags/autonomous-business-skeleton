"""Sales & Revenue Ops demo (deterministic, no infra).

    uv run python -m ab_sales

Leads move through qualify → quote → close; won deals become customer charges that the revenue rail
books to the ledger. Shows the sales → revenue → ledger path end to end.
"""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger
from ab_revenue.core import record_charges
from ab_revenue.gateway import StubRevenueGateway
from ab_sales.core import Lead, run_pipeline, to_charge

LEADS = [
    Lead(business_id="acme", opportunity_id="op1", fit_score=85, budget_minor=120_000, amount_minor=90_000),
    Lead(business_id="acme", opportunity_id="op2", fit_score=40, budget_minor=200_000, amount_minor=50_000),
    Lead(business_id="acme", opportunity_id="op3", fit_score=70, budget_minor=60_000, amount_minor=80_000),
    Lead(business_id="beta", opportunity_id="op4", fit_score=90, budget_minor=150_000, amount_minor=120_000),
]
MIN_FIT = 50
MIN_BUDGET = 10_000


def main() -> int:
    led = InMemoryLedger()
    charges = []
    for lead in LEADS:
        r = run_pipeline(lead, min_fit_score=MIN_FIT, min_budget_minor=MIN_BUDGET)
        print(f"  {r.opportunity_id} {r.business_id:5} [{r.stage.value.upper():4}] {r.reason}")
        result = r
        charge = to_charge(result)
        if charge is not None:
            charges.append(charge)
    record_charges(StubRevenueGateway(charges), led)
    print()
    for bid in ("acme", "beta"):
        print(f"  {bid:5} booked revenue: {led.business_revenue(bid)}")
    print(f"\ntrial balance: {led.trial_balance()} (money conserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
