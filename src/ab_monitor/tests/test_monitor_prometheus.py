"""Prometheus exposition: the same checks + business reads, rendered as gauges (pure)."""

from __future__ import annotations

from ab_monitor.check import CheckResult, CheckStatus, Perfdatum
from ab_monitor.prometheus import business_metrics, check_metrics, exposition
from ab_obs.core import BusinessSnapshot


def _check() -> CheckResult:
    return CheckResult(
        "gateway-slo",
        CheckStatus.WARNING,
        "budget burning",
        (Perfdatum("errors", 9, warn=9, crit=10),),
    )


def _snap() -> BusinessSnapshot:
    return BusinessSnapshot("inboxiq", 250_000, 35_000, 60_000, 115_000, 1_400, "profitable")


def test_check_status_renders_as_a_gauge_with_labels() -> None:
    lines = check_metrics([_check()])
    assert 'ab_check_status{check="gateway-slo"} 1' in lines  # WARNING = 1


def test_perfdata_and_thresholds_render_as_series() -> None:
    lines = check_metrics([_check()])
    assert 'ab_check_perfdata{check="gateway-slo",label="errors"} 9' in lines
    assert 'ab_check_perfdata_warn{check="gateway-slo",label="errors"} 9' in lines
    assert 'ab_check_perfdata_crit{check="gateway-slo",label="errors"} 10' in lines


def test_business_checks_carry_the_business_id_label() -> None:
    result = CheckResult("inboxiq-health", CheckStatus.OK, "healthy", business_id="inboxiq")
    lines = check_metrics([result])
    assert 'ab_check_status{check="inboxiq-health",business_id="inboxiq"} 0' in lines


def test_business_metrics_expose_economics_and_fleet_totals() -> None:
    lines = business_metrics([_snap()])
    assert 'ab_business_revenue_minor{business_id="inboxiq"} 250000' in lines
    assert 'ab_business_operating_profit_minor{business_id="inboxiq"} 115000' in lines
    assert 'ab_business_llm_cost_ratio_bps{business_id="inboxiq"} 1400' in lines
    assert "ab_fleet_businesses 1" in lines
    assert "ab_fleet_unprofitable 0" in lines


def test_exposition_is_newline_terminated_text() -> None:
    text = exposition([_check()], [_snap()])
    assert text.endswith("\n")
    assert "# TYPE ab_check_status gauge" in text
