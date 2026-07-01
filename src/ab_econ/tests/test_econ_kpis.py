"""Extended unit-economics KPIs: contribution margin, LTV, payback, P&L (pure)."""

from __future__ import annotations

from ab_econ.core import UnitInputs, economics, profit_and_loss


def _inputs(**over: int) -> UnitInputs:
    base = dict(
        business_id="acme",
        revenue_minor=1_000_000,
        cogs_minor=200_000,
        ad_spend_minor=200_000,
        llm_spend_minor=50_000,
        customers=100,
    )
    base.update(over)
    return UnitInputs(**base)  # type: ignore[arg-type]


def test_contribution_margin_excludes_acquisition_cost() -> None:
    # revenue − cogs − llm (variable costs); ad spend is acquisition, not a variable cost.
    assert economics(_inputs()).contribution_margin_minor == 750_000  # 1_000_000 − 200_000 − 50_000


def test_ltv_is_per_customer_contribution_times_lifetime() -> None:
    e = economics(_inputs(customers=100), expected_lifetime_periods=12)
    # 750_000 / 100 = 7_500 per customer; × 12 periods = 90_000
    assert e.ltv_minor == 90_000


def test_ltv_is_none_without_customers() -> None:
    assert economics(_inputs(customers=0)).ltv_minor is None


def test_payback_periods_recovers_cac_from_per_customer_contribution() -> None:
    # thin margin: revenue 300_000 → contribution 50_000 → per-customer 500; cac 200_000/100 = 2_000
    e = economics(_inputs(revenue_minor=300_000))
    assert e.cac_minor == 2_000
    assert e.payback_periods == 4  # ceil(2_000 / 500)


def test_payback_is_none_when_contribution_per_customer_is_nonpositive() -> None:
    # llm eats all margin → per-customer contribution ≤ 0 → never pays back
    assert (
        economics(_inputs(revenue_minor=200_000, cogs_minor=150_000, llm_spend_minor=60_000)).payback_periods
        is None
    )


def test_profit_and_loss_rolls_up_the_lines() -> None:
    pnl = profit_and_loss(_inputs())
    assert pnl.revenue_minor == 1_000_000
    assert pnl.gross_profit_minor == 800_000  # revenue − cogs
    assert pnl.contribution_margin_minor == 750_000  # revenue − cogs − llm
    assert pnl.operating_profit_minor == 550_000  # revenue − cogs − llm − ad
