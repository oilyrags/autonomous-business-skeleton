"""Capstone: ledger spend → economics → portfolio allocation, all on real (in-memory) ledger money.

Two businesses both win their experiments (high score), but one is bleeding money once its LLM +
ad spend from the ledger is accounted for. The loop must hold capital from the money-loser even
though its score says "winner". Pure, infra-free.
"""

from __future__ import annotations

from ab_econ.core import UnitInputs, economics, unprofitable_ids
from ab_ledger.core import InMemoryLedger, Posting, Transaction
from ab_portfolio.core import Action, BusinessPerformance, allocate


def _llm_meter(led: InMemoryLedger, bid: str, cost: int, key: str) -> None:
    led.post(
        Transaction(
            txn_id=key,
            idempotency_key=key,
            postings=(Posting(f"{bid}:llm_spend", cost), Posting(f"{bid}:cash", -cost)),
            maker="gateway",
            business_id=bid,
        )
    )


def _ad_payment(led: InMemoryLedger, bid: str, amount: int, key: str) -> None:
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


def _economics(led: InMemoryLedger, bid: str, *, revenue: int, cogs: int, customers: int) -> object:
    spend = led.business_spend(bid)
    return economics(
        UnitInputs(
            business_id=bid,
            revenue_minor=revenue,
            cogs_minor=cogs,
            ad_spend_minor=spend.external_spend_minor,
            llm_spend_minor=spend.llm_spend_minor,
            customers=customers,
        )
    )


def test_allocation_holds_a_winner_that_the_ledger_says_loses_money() -> None:
    led = InMemoryLedger()
    # rocket: modest spend, strong revenue -> profitable.
    _llm_meter(led, "rocket", 20_000, "r-m1")
    _ad_payment(led, "rocket", 50_000, "r-p1")
    # hog: heavy LLM + ad spend, thin revenue -> loses money despite winning experiments.
    # LLM cost accrues per call (maker-only, each within the payment cap), like the live gateway.
    _llm_meter(led, "hog", 100_000, "h-m1")
    _llm_meter(led, "hog", 100_000, "h-m2")
    _ad_payment(led, "hog", 150_000, "h-p1")

    econ = [
        _economics(led, "rocket", revenue=1_000_000, cogs=100_000, customers=100),
        _economics(led, "hog", revenue=300_000, cogs=100_000, customers=40),
    ]
    losers = unprofitable_ids(econ)  # type: ignore[arg-type]
    assert losers == {"hog"}  # the ledger's verdict, not a hand-picked set

    # Both are experiment winners by score; budget is ample so only economics can hold one back.
    performances = [
        BusinessPerformance(business_id="rocket", capital_minor=100_000, scale_count=4),
        BusinessPerformance(business_id="hog", capital_minor=100_000, scale_count=4),
    ]
    recs = allocate(performances, portfolio_budget_minor=1_000_000, unprofitable_business_ids=losers)
    by_id = {r.business_id: r for r in recs}
    assert by_id["rocket"].action is Action.INVEST_MORE
    assert by_id["hog"].action is Action.HOLD and "unprofitable" in by_id["hog"].reason
