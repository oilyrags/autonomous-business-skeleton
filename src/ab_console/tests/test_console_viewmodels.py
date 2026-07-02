"""Fleet view-model: pure aggregation of the existing read-models (infra-free)."""

from __future__ import annotations

from ab_console.viewmodels import fleet, fmt_money
from ab_monitor.check import CheckResult, CheckStatus
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot


def _snap(bid: str, *, profit: int, verdict: str) -> BusinessSnapshot:
    return BusinessSnapshot(bid, 1_000_000, 20_000, 50_000, profit, 500, verdict)


def test_fmt_money_from_integer_minor_units() -> None:
    assert fmt_money(1_000_000) == "€10,000.00"
    assert fmt_money(-30_000) == "-€300.00"
    assert fmt_money(0) == "€0.00"


def test_fleet_totals_aggregate_the_snapshots() -> None:
    view = fleet(
        [
            _snap("rocket", profit=880_000, verdict="profitable"),
            _snap("hog", profit=-30_000, verdict="unprofitable"),
        ],
        anomalies=[],
        checks=[],
        kill_switch_active=False,
    )
    assert view.businesses == 2
    assert view.total_operating_profit_minor == 850_000
    assert view.unprofitable == 1


def test_a_business_with_a_critical_check_shows_critical_and_counts_as_an_alert() -> None:
    checks = [CheckResult("hog-health", CheckStatus.CRITICAL, "operating loss", business_id="hog")]
    view = fleet(
        [
            _snap("rocket", profit=880_000, verdict="profitable"),
            _snap("hog", profit=-30_000, verdict="unprofitable"),
        ],
        anomalies=[Anomaly("hog", AnomalyKind.OPERATING_LOSS, "loss")],
        checks=checks,
        kill_switch_active=False,
    )
    by_id = {r.business_id: r for r in view.rows}
    assert by_id["hog"].status == "CRITICAL"
    assert by_id["rocket"].status == "OK"
    assert view.alert_count == 1


def test_rows_surface_attention_first() -> None:
    checks = [CheckResult("hog-health", CheckStatus.CRITICAL, "loss", business_id="hog")]
    view = fleet(
        [
            _snap("rocket", profit=880_000, verdict="profitable"),
            _snap("hog", profit=-30_000, verdict="unprofitable"),
        ],
        anomalies=[],
        checks=checks,
        kill_switch_active=False,
    )
    assert view.rows[0].business_id == "hog"  # the critical one is first


def test_kill_switch_state_is_reflected() -> None:
    view = fleet([], anomalies=[], checks=[], kill_switch_active=True, kill_switch_reason="drill")
    assert view.kill_switch_active is True and view.kill_switch_reason == "drill"
    assert view.businesses == 0  # empty fleet
