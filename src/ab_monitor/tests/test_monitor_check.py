"""ab_monitor: deterministic checks rendered in the Nagios plugin protocol (pure, infra-free)."""

from __future__ import annotations

from ab_monitor.check import (
    Check,
    CheckResult,
    CheckStatus,
    Perfdatum,
    cert_expiry_check,
    run_all,
    service_check,
    slo_burn_check,
)
from ab_monitor.exporter import StubNagiosExporter, render_all
from ab_ops.reliability import ErrorBudget


def test_check_status_maps_to_nagios_exit_codes() -> None:
    assert (CheckStatus.OK, CheckStatus.WARNING, CheckStatus.CRITICAL, CheckStatus.UNKNOWN) == (0, 1, 2, 3)


def test_perfdatum_renders_label_value_warn_crit() -> None:
    assert Perfdatum(label="days", value=27, warn=30, crit=14).render() == "days=27;30;14"
    assert Perfdatum(label="errors", value=5).render() == "errors=5;;"  # optional warn/crit omitted


def test_check_result_renders_status_output_and_perfdata() -> None:
    r = CheckResult(
        name="mtls-cert",
        status=CheckStatus.WARNING,
        output="cert expires in 27 days",
        perfdata=(Perfdatum(label="days", value=27, warn=30, crit=14),),
    )
    assert r.render() == "WARNING: cert expires in 27 days | days=27;30;14"


def test_service_check_ok_when_healthy_critical_when_down() -> None:
    assert service_check("gateway", healthy=True).status is CheckStatus.OK
    down = service_check("gateway", healthy=False)
    assert down.status is CheckStatus.CRITICAL and "gateway" in down.output


def test_cert_expiry_thresholds() -> None:
    assert (
        cert_expiry_check("gateway", days_remaining=40, warn_days=30, crit_days=14).status is CheckStatus.OK
    )
    assert (
        cert_expiry_check("gateway", days_remaining=20, warn_days=30, crit_days=14).status
        is CheckStatus.WARNING
    )
    assert (
        cert_expiry_check("gateway", days_remaining=10, warn_days=30, crit_days=14).status
        is CheckStatus.CRITICAL
    )


def test_slo_burn_check_reuses_ab_ops_error_budget() -> None:
    budget = ErrorBudget(slo_target=0.99, window=1000)  # budget = 10 errors
    assert slo_burn_check("gateway", budget, errors=3).status is CheckStatus.OK
    assert slo_burn_check("gateway", budget, errors=9).status is CheckStatus.WARNING  # >= 90% of budget
    assert slo_burn_check("gateway", budget, errors=25).status is CheckStatus.CRITICAL  # exhausted


def test_run_all_executes_checks_and_stub_exporter_records() -> None:
    checks = [
        Check(name="gateway-up", run=lambda: service_check("gateway", healthy=True)),
        Check(name="agent-up", run=lambda: service_check("agent", healthy=False)),
    ]
    results = run_all(checks)
    assert [r.status for r in results] == [CheckStatus.OK, CheckStatus.CRITICAL]

    exporter = StubNagiosExporter()
    exporter.export(results)
    assert len(exporter.submitted) == 2
    assert render_all(results).splitlines()[1].startswith("CRITICAL:")
