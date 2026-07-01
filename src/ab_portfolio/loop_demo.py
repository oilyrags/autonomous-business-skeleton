"""End-to-end loop demo (deterministic, no infra): ledger → econ → portfolio.

    uv run python -m ab_portfolio.loop_demo

Per-business spend is read from the ledger, turned into a profitability verdict by ab_econ, and the
loss-makers are held back from new capital by the allocator — even when their experiment score says
"winner". Two businesses both win their experiments; only the ledger tells them apart.
"""

from __future__ import annotations

from ab_econ.core import UnitInputs, economics, unprofitable_ids
from ab_ledger.core import InMemoryLedger, Posting, Transaction
from ab_portfolio.core import BusinessPerformance, allocate
from ab_revenue.core import Charge, record_charges
from ab_revenue.gateway import StubRevenueGateway

# cogs + customers still come from a rail (injected); revenue AND spend now come from the ledger.
COGS_AND_CUSTOMERS = {"rocket": (100_000, 100), "hog": (100_000, 40)}  # cogs_minor, customers
REVENUE_CHARGES = [
    Charge(business_id="rocket", amount_minor=1_000_000, customer_ref="cus_r", external_ref="rev_r"),
    Charge(business_id="hog", amount_minor=300_000, customer_ref="cus_h", external_ref="rev_h"),
]
BUDGET_MINOR = 1_000_000


def _seed_ledger() -> InMemoryLedger:
    led = InMemoryLedger()

    def meter(bid: str, cost: int, key: str) -> None:
        led.post(
            Transaction(
                txn_id=key,
                idempotency_key=key,
                postings=(Posting(f"{bid}:llm_spend", cost), Posting(f"{bid}:cash", -cost)),
                maker="gateway",
                business_id=bid,
            )
        )

    def ad(bid: str, amount: int, key: str) -> None:
        led.post(
            Transaction(
                txn_id=key,
                idempotency_key=key,
                postings=(Posting("external:ads_co", amount), Posting(f"{bid}:cash", -amount)),
                maker="agent",
                checker="controller",
                business_id=bid,
                payee="ads_co",
            )
        )

    meter("rocket", 20_000, "r-m1")
    ad("rocket", 50_000, "r-p1")
    meter("hog", 100_000, "h-m1")
    meter("hog", 100_000, "h-m2")
    ad("hog", 150_000, "h-p1")
    record_charges(StubRevenueGateway(REVENUE_CHARGES), led)  # customer revenue -> the ledger
    return led


def main() -> int:
    led = _seed_ledger()
    econ = []
    for bid, (cogs, customers) in COGS_AND_CUSTOMERS.items():
        spend = led.business_spend(bid)
        revenue = led.business_revenue(bid)  # real income from the ledger, not injected
        e = economics(
            UnitInputs(
                business_id=bid,
                revenue_minor=revenue,
                cogs_minor=cogs,
                ad_spend_minor=spend.external_spend_minor,
                llm_spend_minor=spend.llm_spend_minor,
                customers=customers,
            )
        )
        econ.append(e)
        print(
            f"  {bid:8} ledger: revenue={revenue} llm={spend.llm_spend_minor} "
            f"ad={spend.external_spend_minor} -> profit={e.operating_profit_minor:+8} "
            f"[{e.verdict.value.upper()}]"
        )

    losers = unprofitable_ids(econ)
    print(f"\n  unprofitable (from the ledger): {sorted(losers) or '—'}")

    # Both businesses are experiment winners by score; only economics separates them.
    performances = [
        BusinessPerformance(business_id="rocket", capital_minor=100_000, scale_count=4),
        BusinessPerformance(business_id="hog", capital_minor=100_000, scale_count=4),
    ]
    print()
    for r in allocate(performances, portfolio_budget_minor=BUDGET_MINOR, unprofitable_business_ids=losers):
        print(f"  [{r.action.value.upper():11}] {r.business_id:8} Δ={r.capital_delta:+8} — {r.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
