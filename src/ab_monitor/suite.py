"""A representative check suite (platform + invariants + per-business), shared by the demo and the
submit entrypoint. In production the injected values come from live probes (health endpoints, the
ledger, the kill switch, ab_obs snapshots); here they are deterministic sample values so the
pipeline — evaluate → render → export — can be exercised end to end.
"""

from __future__ import annotations

from ab_monitor.business import business_checks, dsar_backlog_check
from ab_monitor.check import Check, CheckResult, cert_expiry_check, run_all, service_check, slo_burn_check
from ab_monitor.invariants import audit_integrity_check, kill_switch_check, ledger_balance_check
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot
from ab_ops.reliability import ErrorBudget

_GATEWAY_BUDGET = ErrorBudget(slo_target=0.99, window=1000)  # 10 errors allowed

_PLATFORM_CHECKS = [
    Check("gateway-up", lambda: service_check("gateway", healthy=True)),
    Check("identity-up", lambda: service_check("identity", healthy=False)),  # injected outage
    Check("gateway-mtls", lambda: cert_expiry_check("gateway", days_remaining=9, warn_days=30, crit_days=14)),
    Check("gateway-slo", lambda: slo_burn_check("gateway", _GATEWAY_BUDGET, errors=25)),
    Check("ledger-balance", lambda: ledger_balance_check(trial_balance=0)),
    Check("audit-integrity", lambda: audit_integrity_check(intact=True, entries_verified=1200)),
    Check("kill-switch", lambda: kill_switch_check(active=False)),
    Check("dsar-backlog", lambda: dsar_backlog_check(oldest_open_days=29, warn_days=21, crit_days=28)),
]

_SNAPSHOTS = [
    BusinessSnapshot("rocket", 1_000_000, 20_000, 50_000, 880_000, 500, "profitable"),
    BusinessSnapshot("hog", 250_000, 200_000, 0, -30_000, 8_000, "unprofitable"),
]
_ANOMALIES = [Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating profit -30000 < floor -10000")]


def demo_suite() -> list[CheckResult]:
    """The full sample check suite as CheckResults, ready to render or export."""
    return run_all(_PLATFORM_CHECKS) + business_checks(_SNAPSHOTS, _ANOMALIES)
