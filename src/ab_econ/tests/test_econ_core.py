"""Per-business unit economics (pure, integer minor units)."""

from __future__ import annotations

from ab_econ.core import UnitInputs, Verdict, economics, within_llm_budget


def _inputs(**over: int) -> UnitInputs:
    base = dict(
        business_id="acme",
        revenue_minor=1_000_000,
        cogs_minor=200_000,
        ad_spend_minor=100_000,
        llm_spend_minor=50_000,
        customers=100,
    )
    base.update(over)
    return UnitInputs(**base)  # type: ignore[arg-type]


def test_profitable_business() -> None:
    e = economics(_inputs())
    # 1_000_000 − 200_000 − 100_000 − 50_000 = 650_000
    assert e.operating_profit_minor == 650_000
    assert e.verdict is Verdict.PROFITABLE


def test_cac_is_ad_spend_per_customer_and_none_without_customers() -> None:
    assert economics(_inputs(ad_spend_minor=100_000, customers=100)).cac_minor == 1_000
    assert economics(_inputs(customers=0)).cac_minor is None


def test_gross_margin_bps_excludes_ad_but_counts_cogs_and_llm() -> None:
    # (1_000_000 − 200_000 − 50_000) / 1_000_000 = 0.75 → 7_500 bps
    assert economics(_inputs()).gross_margin_bps == 7_500
    assert economics(_inputs(revenue_minor=0)).gross_margin_bps is None


def test_llm_cost_ratio_bps_is_llm_share_of_revenue() -> None:
    # 50_000 / 1_000_000 = 0.05 → 500 bps
    assert economics(_inputs()).llm_cost_ratio_bps == 500
    assert economics(_inputs(revenue_minor=0)).llm_cost_ratio_bps is None


def test_loss_making_business_is_unprofitable() -> None:
    # revenue 100_000 vs 200_000+100_000+50_000 costs → −250_000
    e = economics(_inputs(revenue_minor=100_000))
    assert e.operating_profit_minor == -250_000
    assert e.verdict is Verdict.UNPROFITABLE


def test_within_llm_budget_guard() -> None:
    at_budget = _inputs(llm_spend_minor=50_000)
    assert within_llm_budget(at_budget, llm_budget_minor=50_000) is True  # at budget
    assert within_llm_budget(at_budget, llm_budget_minor=49_999) is False  # over budget
    assert within_llm_budget(at_budget, llm_budget_minor=60_000) is True  # under budget
