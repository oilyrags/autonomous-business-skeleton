"""Audit 12: every implemented failure-injection scenario contains its failure."""

from ab_failsim import __main__ as cli
from ab_failsim.scenarios import run_all


def test_all_scenarios_run() -> None:
    results = run_all()
    assert len(results) == 7


def test_no_breaches_in_implemented_scenarios() -> None:
    breaches = [r for r in run_all() if not r.deferred and not r.contained]
    assert breaches == []


def test_implemented_scenarios_are_contained() -> None:
    contained = {r.name for r in run_all() if not r.deferred and r.contained}
    assert contained == {
        "bad_model_output",
        "hostile_prompt_injection",
        "bad_payment",
        "failed_dependency",
        "stale_forecast",
    }


def test_only_dsar_and_incident_are_deferred() -> None:
    deferred = {r.name for r in run_all() if r.deferred}
    assert deferred == {"dsar_erasure_with_legal_hold", "incident_rollback"}


def test_cli_exits_zero_when_no_breaches() -> None:
    assert cli.main() == 0
