"""Per-business checks from ab_obs anomalies + DSAR backlog (pure, infra-free)."""

from __future__ import annotations

from ab_monitor.business import business_checks, dsar_backlog_check
from ab_monitor.check import CheckStatus
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot


def _snap(bid: str, *, profit: int, verdict: str, llm_ratio: int | None = 500) -> BusinessSnapshot:
    return BusinessSnapshot(
        business_id=bid,
        revenue_minor=1_000_000,
        llm_spend_minor=20_000,
        ad_spend_minor=50_000,
        operating_profit_minor=profit,
        llm_cost_ratio_bps=llm_ratio,
        verdict=verdict,
    )


def test_healthy_business_is_ok_and_tagged() -> None:
    (r,) = business_checks([_snap("rocket", profit=880_000, verdict="profitable")], anomalies=[])
    assert r.status is CheckStatus.OK
    assert r.business_id == "rocket" and "rocket" in r.output


def test_operating_loss_anomaly_is_critical() -> None:
    snap = _snap("hog", profit=-30_000, verdict="unprofitable")
    anomaly = Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating profit -30000 < floor -10000")
    (r,) = business_checks([snap], anomalies=[anomaly])
    assert r.status is CheckStatus.CRITICAL and r.business_id == "hog"


def test_worst_anomaly_wins_across_kinds() -> None:
    snap = _snap("hog", profit=-30_000, verdict="unprofitable")
    anomalies = [
        Anomaly("hog", AnomalyKind.LLM_COST_HIGH, "llm cost 8000bps"),
        Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating loss"),
    ]
    (r,) = business_checks([snap], anomalies=anomalies)
    assert r.status is CheckStatus.CRITICAL  # CRITICAL beats WARNING


def test_llm_cost_high_alone_is_a_warning() -> None:
    snap = _snap("pricey", profit=5_000, verdict="profitable", llm_ratio=8_000)
    anomaly = Anomaly("pricey", AnomalyKind.LLM_COST_HIGH, "llm cost 8000bps > 2000bps")
    (r,) = business_checks([snap], anomalies=[anomaly])
    assert r.status is CheckStatus.WARNING


def test_dsar_backlog_thresholds() -> None:
    assert dsar_backlog_check(oldest_open_days=5, warn_days=21, crit_days=28).status is CheckStatus.OK
    assert dsar_backlog_check(oldest_open_days=22, warn_days=21, crit_days=28).status is CheckStatus.WARNING
    assert dsar_backlog_check(oldest_open_days=29, warn_days=21, crit_days=28).status is CheckStatus.CRITICAL
