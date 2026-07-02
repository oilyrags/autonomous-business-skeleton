"""Monitoring demo (deterministic, no infra).

    uv run python -m ab_monitor

Evaluates a suite of deterministic checks (service liveness, mTLS cert expiry, SLO error-budget burn)
and emits them in the Nagios plugin protocol — the same lines Nagios Core / Icinga2 / Naemon consume.
A real submit adapter (NSCA / Icinga2 REST) slots in behind the NagiosExporter port.
"""

from __future__ import annotations

from ab_monitor.check import Check, cert_expiry_check, run_all, service_check, slo_burn_check
from ab_monitor.exporter import StubNagiosExporter, render_all
from ab_ops.reliability import ErrorBudget

GATEWAY_BUDGET = ErrorBudget(slo_target=0.99, window=1000)  # 10 errors allowed

CHECKS = [
    Check("gateway-up", lambda: service_check("gateway", healthy=True)),
    Check("agent-up", lambda: service_check("agent", healthy=True)),
    Check("identity-up", lambda: service_check("identity", healthy=False)),  # injected outage
    Check("gateway-mtls", lambda: cert_expiry_check("gateway", days_remaining=9, warn_days=30, crit_days=14)),
    Check("agent-mtls", lambda: cert_expiry_check("agent", days_remaining=45, warn_days=30, crit_days=14)),
    Check("gateway-slo", lambda: slo_burn_check("gateway", GATEWAY_BUDGET, errors=25)),
]


def main() -> int:
    results = run_all(CHECKS)
    print(render_all(results))
    StubNagiosExporter().export(results)  # a real adapter would submit these to Nagios/Icinga2
    crit = sum(1 for r in results if r.status.name == "CRITICAL")
    warn = sum(1 for r in results if r.status.name == "WARNING")
    print(f"\n  {len(results)} checks: {crit} CRITICAL, {warn} WARNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
