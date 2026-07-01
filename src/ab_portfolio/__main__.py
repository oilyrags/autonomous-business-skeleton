"""Portfolio capital-allocation demo (deterministic, no infra).

    uv run python -m ab_portfolio

Recommends a capital action per business — recycling capital from losers into winners within
the portfolio budget cap. Recommend-only; capital moves are human-in-the-loop.
"""

from __future__ import annotations

from ab_portfolio.core import BusinessPerformance, allocate

# A small portfolio: two winners, a conclusive loser, a marginal loser, and a neutral business.
PORTFOLIO = [
    BusinessPerformance(business_id="rocket", capital_minor=100_000, scale_count=4, kill_count=0),
    BusinessPerformance(business_id="steady", capital_minor=100_000, scale_count=2, kill_count=0),
    BusinessPerformance(business_id="sinker", capital_minor=200_000, scale_count=0, kill_count=3),
    BusinessPerformance(business_id="wobble", capital_minor=100_000, scale_count=0, kill_count=1),
    BusinessPerformance(business_id="early", capital_minor=100_000, scale_count=1, pivot_count=1),
]
PORTFOLIO_BUDGET_MINOR = 500_000  # tight: only one winner's increment of headroom after the reclaim


def main() -> int:
    recs = allocate(PORTFOLIO, portfolio_budget_minor=PORTFOLIO_BUDGET_MINOR)
    deployed = sum(p.capital_minor for p in PORTFOLIO)
    for r in recs:
        print(f"  [{r.action.value.upper():11}] {r.business_id:8} Δcapital={r.capital_delta:+8} — {r.reason}")
    net = deployed + sum(r.capital_delta for r in recs)
    within = net <= PORTFOLIO_BUDGET_MINOR
    print(f"\ndeployed {deployed} → {net} (budget {PORTFOLIO_BUDGET_MINOR}); within cap: {within}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
