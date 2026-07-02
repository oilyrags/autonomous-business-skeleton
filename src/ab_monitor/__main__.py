"""Monitoring demo (deterministic, no infra).

    uv run python -m ab_monitor

Evaluates the deterministic check suite — service liveness, mTLS expiry, SLO burn, the money/audit/
kill-switch invariants, and per-business health (reusing ab_obs) — and emits them in the Nagios
plugin protocol. A real submit adapter (NSCA / Icinga2 REST) slots in behind the NagiosExporter port.
"""

from __future__ import annotations

from ab_monitor.business import business_checks, dsar_backlog_check
from ab_monitor.check import Check, CheckResult, cert_expiry_check, run_all, service_check, slo_burn_check
from ab_monitor.exporter import StubNagiosExporter, render_all
from ab_monitor.invariants import audit_integrity_check, kill_switch_check, ledger_balance_check
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot
from ab_ops.reliability import ErrorBudget

GATEWAY_BUDGET = ErrorBudget(slo_target=0.99, window=1000)  # 10 errors allowed

PLATFORM_CHECKS = [
    Check("gateway-up", lambda: service_check("gateway", healthy=True)),
    Check("identity-up", lambda: service_check("identity", healthy=False)),  # injected outage
    Check("gateway-mtls", lambda: cert_expiry_check("gateway", days_remaining=9, warn_days=30, crit_days=14)),
    Check("gateway-slo", lambda: slo_burn_check("gateway", GATEWAY_BUDGET, errors=25)),
    Check("ledger-balance", lambda: ledger_balance_check(trial_balance=0)),
    Check("audit-integrity", lambda: audit_integrity_check(intact=True, entries_verified=1200)),
    Check("kill-switch", lambda: kill_switch_check(active=False)),
    Check("dsar-backlog", lambda: dsar_backlog_check(oldest_open_days=29, warn_days=21, crit_days=28)),
]

# Per-business health, reusing ab_obs snapshots + anomalies (rocket healthy; hog bleeding).
SNAPSHOTS = [
    BusinessSnapshot("rocket", 1_000_000, 20_000, 50_000, 880_000, 500, "profitable"),
    BusinessSnapshot("hog", 250_000, 200_000, 0, -30_000, 8_000, "unprofitable"),
]
ANOMALIES = [Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating profit -30000 < floor -10000")]


def main() -> int:
    results: list[CheckResult] = run_all(PLATFORM_CHECKS) + business_checks(SNAPSHOTS, ANOMALIES)
    print(render_all(results))
    StubNagiosExporter().export(results)  # a real adapter would submit these to Nagios/Icinga2
    crit = sum(1 for r in results if r.status.name == "CRITICAL")
    warn = sum(1 for r in results if r.status.name == "WARNING")
    print(f"\n  {len(results)} checks: {crit} CRITICAL, {warn} WARNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
