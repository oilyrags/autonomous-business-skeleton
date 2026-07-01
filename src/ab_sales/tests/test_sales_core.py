"""Sales pipeline: qualify → quote → close, and a won deal becomes revenue (pure, infra-free)."""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger
from ab_revenue.core import record_charges
from ab_revenue.gateway import StubRevenueGateway
from ab_sales.core import Lead, Stage, expansion_charge, run_pipeline, to_charge, to_event


def _lead(*, fit: int = 80, budget: int = 100_000, amount: int = 80_000, oid: str = "op1") -> Lead:
    return Lead(
        business_id="acme", opportunity_id=oid, fit_score=fit, budget_minor=budget, amount_minor=amount
    )


def test_a_good_fit_within_budget_is_won() -> None:
    r = run_pipeline(_lead(fit=80, budget=100_000, amount=80_000), min_fit_score=50, min_budget_minor=10_000)
    assert r.stage is Stage.WON
    assert r.amount_minor == 80_000


def test_low_fit_is_lost_unqualified() -> None:
    r = run_pipeline(_lead(fit=20), min_fit_score=50, min_budget_minor=10_000)
    assert r.stage is Stage.LOST and "fit" in r.reason


def test_quote_over_budget_is_lost() -> None:
    r = run_pipeline(_lead(budget=50_000, amount=80_000), min_fit_score=50, min_budget_minor=10_000)
    assert r.stage is Stage.LOST and "exceeds budget" in r.reason


def test_won_sale_becomes_a_charge_and_lost_does_not() -> None:
    won = run_pipeline(_lead(amount=60_000), min_fit_score=50, min_budget_minor=10_000)
    assert to_charge(won) is not None and to_charge(won).amount_minor == 60_000  # type: ignore[union-attr]
    lost = run_pipeline(_lead(fit=10), min_fit_score=50, min_budget_minor=10_000)
    assert to_charge(lost) is None


def test_won_sale_booked_through_revenue_hits_the_ledger() -> None:
    led = InMemoryLedger()
    won = run_pipeline(_lead(amount=90_000, oid="deal1"), min_fit_score=50, min_budget_minor=10_000)
    charge = to_charge(won)
    assert charge is not None
    record_charges(StubRevenueGateway([charge]), led)  # book the won sale as revenue
    assert led.business_revenue("acme") == 90_000
    assert led.trial_balance() == 0


def test_expansion_charges_only_a_won_account() -> None:
    won = run_pipeline(_lead(oid="acc1"), min_fit_score=50, min_budget_minor=10_000)
    assert expansion_charge(won, uplift_minor=20_000).amount_minor == 20_000  # type: ignore[union-attr]
    lost = run_pipeline(_lead(fit=10), min_fit_score=50, min_budget_minor=10_000)
    assert expansion_charge(lost, uplift_minor=20_000) is None


def test_sale_becomes_a_business_scoped_event() -> None:
    ev = to_event(run_pipeline(_lead(oid="op9"), min_fit_score=50, min_budget_minor=10_000))
    assert ev.event_name == "SaleClosed" and ev.business_id == "acme"
    assert ev.stage == "won" and ev.opportunity_id == "op9"
