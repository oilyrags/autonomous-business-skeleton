"""Per-business spend derived from the ledger (pure, InMemoryLedger)."""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger, LedgerSpend, Posting, Transaction


def _llm_meter(bid: str, cost: int, *, key: str) -> Transaction:
    """The gateway's LLM-metering shape: debit {bid}:llm_spend, credit {bid}:cash."""
    return Transaction(
        txn_id=key,
        idempotency_key=key,
        postings=(Posting(f"{bid}:llm_spend", cost), Posting(f"{bid}:cash", -cost)),
        maker="gateway",
        business_id=bid,
    )


def _external_payment(bid: str, amount: int, payee: str, *, key: str) -> Transaction:
    """A business-scoped external payment: debit external:<payee>, credit {bid}:cash."""
    return Transaction(
        txn_id=key,
        idempotency_key=key,
        postings=(Posting(f"external:{payee}", amount), Posting(f"{bid}:cash", -amount)),
        maker="agent",
        checker="controller",  # unlisted payee → maker-checker approval
        business_id=bid,
        payee=payee,
    )


def test_business_spend_splits_llm_and_external() -> None:
    led = InMemoryLedger()
    led.post(_llm_meter("acme", 12_000, key="m1"))
    led.post(_llm_meter("acme", 8_000, key="m2"))
    led.post(_external_payment("acme", 30_000, "ads_co", key="p1"))

    spend = led.business_spend("acme")
    assert spend == LedgerSpend(business_id="acme", llm_spend_minor=20_000, external_spend_minor=30_000)


def test_business_spend_is_isolated_per_business() -> None:
    led = InMemoryLedger()
    led.post(_llm_meter("acme", 20_000, key="a1"))
    led.post(_external_payment("beta", 50_000, "ads_co", key="b1"))

    assert led.business_spend("acme") == LedgerSpend("acme", 20_000, 0)
    assert led.business_spend("beta") == LedgerSpend("beta", 0, 50_000)


def test_business_with_no_activity_has_zero_spend() -> None:
    assert InMemoryLedger().business_spend("ghost") == LedgerSpend("ghost", 0, 0)


def test_ledger_spend_feeds_unit_economics() -> None:
    from ab_econ.core import UnitInputs, Verdict, economics

    led = InMemoryLedger()
    led.post(_llm_meter("acme", 20_000, key="m1"))
    led.post(_external_payment("acme", 100_000, "ads_co", key="p1"))
    spend = led.business_spend("acme")

    # Revenue/customers still come from a rail; spend now comes from the ledger.
    e = economics(
        UnitInputs(
            business_id="acme",
            revenue_minor=1_000_000,
            cogs_minor=200_000,
            ad_spend_minor=spend.external_spend_minor,
            llm_spend_minor=spend.llm_spend_minor,
            customers=100,
        )
    )
    # 1_000_000 − 200_000 − 100_000 (ad) − 20_000 (llm) = 680_000
    assert e.operating_profit_minor == 680_000
    assert e.verdict is Verdict.PROFITABLE
    assert e.cac_minor == 1_000  # 100_000 ad spend / 100 customers
