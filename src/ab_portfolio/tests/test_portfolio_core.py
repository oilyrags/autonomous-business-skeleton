"""Portfolio capital-allocation engine (pure, infra-free)."""

from ab_portfolio.core import Action, BusinessPerformance, allocate


def _perf(bid: str, *, capital: int, scale: int = 0, pivot: int = 0, kill: int = 0) -> BusinessPerformance:
    return BusinessPerformance(
        business_id=bid, capital_minor=capital, scale_count=scale, pivot_count=pivot, kill_count=kill
    )


def test_conclusive_winner_with_capacity_gets_invest_more() -> None:
    recs = allocate([_perf("w", capital=100_000, scale=3)], portfolio_budget_minor=1_000_000)
    assert len(recs) == 1
    assert recs[0].business_id == "w"
    assert recs[0].action is Action.INVEST_MORE
    assert recs[0].capital_delta > 0


def test_conclusive_loser_is_sunset_reclaiming_its_capital() -> None:
    recs = allocate([_perf("loser", capital=250_000, scale=0, kill=3)], portfolio_budget_minor=1_000_000)
    assert recs[0].action is Action.SUNSET
    assert recs[0].capital_delta == -250_000  # reclaim the deployed capital


def test_marginal_loser_starves_and_neutral_holds() -> None:
    recs = allocate(
        [
            _perf("marginal", capital=100_000, scale=0, kill=1),  # score -1, only 1 experiment
            _perf("neutral", capital=100_000, scale=1, pivot=1),  # score 1, below invest threshold
        ],
        portfolio_budget_minor=1_000_000,
    )
    by_id = {r.business_id: r for r in recs}
    assert by_id["marginal"].action is Action.STARVE and by_id["marginal"].capital_delta == 0
    assert by_id["neutral"].action is Action.HOLD and by_id["neutral"].capital_delta == 0


def test_winner_beyond_the_budget_cap_is_held() -> None:
    # Two winners; only one increment of headroom -> the higher-score one is funded, the other held.
    recs = allocate(
        [_perf("A", capital=100_000, scale=3), _perf("B", capital=100_000, scale=2)],
        portfolio_budget_minor=300_000,  # available = 300k - 200k deployed = 100k = one increment
        reinvest_increment_minor=100_000,
    )
    by_id = {r.business_id: r for r in recs}
    assert by_id["A"].action is Action.INVEST_MORE  # higher score funded first
    assert by_id["B"].action is Action.HOLD and "budget" in by_id["B"].reason


def test_sunset_frees_capacity_to_fund_a_winner() -> None:
    # Fully-deployed portfolio: only sunsetting the loser frees room to fund the winner.
    recs = allocate(
        [
            _perf("loser", capital=200_000, kill=3),  # SUNSET -> reclaims 200k
            _perf("winner", capital=100_000, scale=3),  # needs 100k it couldn't get otherwise
        ],
        portfolio_budget_minor=300_000,  # == total deployed; no free room without the reclaim
        reinvest_increment_minor=100_000,
    )
    by_id = {r.business_id: r for r in recs}
    assert by_id["loser"].action is Action.SUNSET
    assert by_id["winner"].action is Action.INVEST_MORE  # funded by the reclaimed capital
    # Net deployment after applying deltas stays within budget.
    net_deployed = 300_000 + sum(r.capital_delta for r in recs)
    assert net_deployed <= 300_000


def test_recommendations_become_business_scoped_events() -> None:
    from ab_portfolio.core import to_events

    recs = allocate([_perf("w", capital=100_000, scale=3)], portfolio_budget_minor=1_000_000)
    events = to_events(recs)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_name == "CapitalReallocationRecommended"
    assert ev.business_id == "w" and ev.action == "invest_more" and ev.capital_delta > 0
