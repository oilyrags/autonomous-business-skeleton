"""Per-business unit-economics demo (deterministic, no infra).

    uv run python -m ab_econ

Two businesses: one healthy, one bleeding on LLM inference cost. Shows the KPIs (operating
profit, CAC, gross margin, LLM cost ratio) + the verdict, and the per-business LLM budget guard.
Report-only; no ledger writes.
"""

from __future__ import annotations

from ab_econ.core import UnitInputs, economics, within_llm_budget

PORTFOLIO = [
    UnitInputs(
        business_id="healthy",
        revenue_minor=1_000_000,
        cogs_minor=200_000,
        ad_spend_minor=100_000,
        llm_spend_minor=50_000,
        customers=100,
    ),
    UnitInputs(
        business_id="llm_hog",
        revenue_minor=300_000,
        cogs_minor=80_000,
        ad_spend_minor=120_000,
        llm_spend_minor=250_000,
        customers=40,
    ),
]
LLM_BUDGET_MINOR = 100_000  # per-business inference budget


def _fmt(v: int | None) -> str:
    return "n/a" if v is None else str(v)


def main() -> int:
    for i in PORTFOLIO:
        e = economics(i)
        ok = within_llm_budget(i, llm_budget_minor=LLM_BUDGET_MINOR)
        print(
            f"  {e.business_id:8} profit={e.operating_profit_minor:+8} "
            f"cac={_fmt(e.cac_minor):>6} margin_bps={_fmt(e.gross_margin_bps):>6} "
            f"llm_ratio_bps={_fmt(e.llm_cost_ratio_bps):>6} "
            f"[{e.verdict.value.upper()}] llm_budget_ok={ok}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
