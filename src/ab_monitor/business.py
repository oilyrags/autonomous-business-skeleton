"""Per-business health checks (pure): a struggling business shows up in monitoring, not just
finance. Reuses `ab_obs` — its anomalies map to Nagios statuses — rather than reinventing the
signal. Every result is tagged with its ``business_id`` so a new business is monitored automatically.
"""

from __future__ import annotations

from collections.abc import Iterable

from ab_monitor.check import CheckResult, CheckStatus, Perfdatum
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot

_ANOMALY_STATUS: dict[AnomalyKind, CheckStatus] = {
    AnomalyKind.OPERATING_LOSS: CheckStatus.CRITICAL,
    AnomalyKind.LLM_COST_HIGH: CheckStatus.WARNING,
}


def business_checks(snapshots: Iterable[BusinessSnapshot], anomalies: Iterable[Anomaly]) -> list[CheckResult]:
    """One health check per business: OK when clean, else the worst of its `ab_obs` anomalies."""
    by_business: dict[str, list[Anomaly]] = {}
    for a in anomalies:
        by_business.setdefault(a.business_id, []).append(a)

    results: list[CheckResult] = []
    for s in snapshots:
        found = by_business.get(s.business_id, [])
        if found:
            status = max(_ANOMALY_STATUS[a.kind] for a in found)  # worst wins (CRITICAL > WARNING)
            output = "; ".join(a.detail for a in found)
        else:
            status = CheckStatus.OK
            output = f"{s.business_id} healthy ({s.verdict})"
        perf = (
            Perfdatum("operating_profit", s.operating_profit_minor),
            Perfdatum("llm_cost_ratio_bps", s.llm_cost_ratio_bps or 0),
        )
        results.append(
            CheckResult(f"{s.business_id}-health", status, output, perf, business_id=s.business_id)
        )
    return results


def dsar_backlog_check(
    *, oldest_open_days: int, warn_days: int, crit_days: int, business_id: str | None = None
) -> CheckResult:
    """The oldest open DSAR must be actioned before its statutory deadline — warn early, crit late."""
    perf = (Perfdatum("oldest_open_days", oldest_open_days, warn_days, crit_days),)
    if oldest_open_days >= crit_days:
        status = CheckStatus.CRITICAL
    elif oldest_open_days >= warn_days:
        status = CheckStatus.WARNING
    else:
        status = CheckStatus.OK
    return CheckResult(
        "dsar-backlog", status, f"oldest open DSAR is {oldest_open_days}d old", perf, business_id=business_id
    )
