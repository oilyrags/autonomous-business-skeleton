"""Property-based tests for the portfolio allocator's capital invariants (pure, infra-free).

`allocate` recycles capital between businesses; the money-critical guarantees are that it never
deploys *new* capital past the budget headroom, that a sunset reclaims exactly the business's
capital, and that every business gets exactly one recommendation in input order. These check those
hold for arbitrary portfolios, not just the hand-picked unit-test cases.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ab_portfolio.core import Action, BusinessPerformance, allocate

# A business: (capital, scale, pivot, kill). ids are assigned by index so they are unique.
_BUSINESS = st.tuples(
    st.integers(min_value=0, max_value=1_000_000),
    st.integers(min_value=0, max_value=8),
    st.integers(min_value=0, max_value=8),
    st.integers(min_value=0, max_value=8),
)


def _perfs(rows: list[tuple[int, int, int, int]]) -> list[BusinessPerformance]:
    return [
        BusinessPerformance(
            business_id=f"b{i}", capital_minor=cap, scale_count=s, pivot_count=p, kill_count=k
        )
        for i, (cap, s, p, k) in enumerate(rows)
    ]


_PORTFOLIO = st.lists(_BUSINESS, max_size=15)
_BUDGET = st.integers(min_value=0, max_value=3_000_000)
_INCREMENT = st.integers(min_value=1, max_value=500_000)


@given(rows=_PORTFOLIO, budget=_BUDGET, increment=_INCREMENT)
def test_every_business_gets_one_recommendation_in_order(
    rows: list[tuple[int, int, int, int]], budget: int, increment: int
) -> None:
    perfs = _perfs(rows)
    recs = allocate(perfs, portfolio_budget_minor=budget, reinvest_increment_minor=increment)
    assert [r.business_id for r in recs] == [p.business_id for p in perfs]


@given(rows=_PORTFOLIO, budget=_BUDGET, increment=_INCREMENT)
def test_sunset_reclaims_exactly_the_business_capital(
    rows: list[tuple[int, int, int, int]], budget: int, increment: int
) -> None:
    perfs = _perfs(rows)
    by_id = {p.business_id: p for p in perfs}
    recs = allocate(perfs, portfolio_budget_minor=budget, reinvest_increment_minor=increment)
    for r in recs:
        if r.action is Action.SUNSET:
            assert r.capital_delta == -by_id[r.business_id].capital_minor


@given(rows=_PORTFOLIO, budget=_BUDGET, increment=_INCREMENT)
def test_new_capital_never_exceeds_the_budget_headroom(
    rows: list[tuple[int, int, int, int]], budget: int, increment: int
) -> None:
    perfs = _perfs(rows)
    recs = allocate(perfs, portfolio_budget_minor=budget, reinvest_increment_minor=increment)
    deployed = sum(p.capital_minor for p in perfs)
    reclaimed = -sum(r.capital_delta for r in recs if r.action is Action.SUNSET)
    invested = sum(r.capital_delta for r in recs if r.action is Action.INVEST_MORE)
    # New capital is bounded by the headroom left after sunsets free their capital.
    assert invested <= max(0, budget - (deployed - reclaimed))
    # Consequently net deployment never rises above the cap when it started within it.
    net = deployed - reclaimed + invested
    if deployed <= budget:
        assert net <= budget


@given(rows=_PORTFOLIO, budget=_BUDGET, increment=_INCREMENT)
def test_only_invest_and_sunset_move_capital(
    rows: list[tuple[int, int, int, int]], budget: int, increment: int
) -> None:
    perfs = _perfs(rows)
    recs = allocate(perfs, portfolio_budget_minor=budget, reinvest_increment_minor=increment)
    for r in recs:
        if r.action in (Action.HOLD, Action.STARVE):
            assert r.capital_delta == 0
        elif r.action is Action.INVEST_MORE:
            assert r.capital_delta == increment
