"""Audit 12: every implemented failure-injection scenario contains its failure."""

from ab_failsim import __main__ as cli
from ab_failsim.scenarios import run_all


def test_all_scenarios_run() -> None:
    results = run_all()
    assert len(results) == 7


def test_no_breaches_in_implemented_scenarios() -> None:
    breaches = [r for r in run_all() if not r.deferred and not r.contained]
    assert breaches == []


def test_all_seven_scenarios_are_contained() -> None:
    results = run_all()
    assert all(r.contained for r in results)  # every scenario's control contains its failure


def test_no_scenarios_remain_deferred() -> None:
    assert [r.name for r in run_all() if r.deferred] == []


def test_cli_exits_zero_when_no_breaches() -> None:
    assert cli.main() == 0
