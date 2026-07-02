"""Monitoring demo (deterministic, no infra).

    uv run python -m ab_monitor

Evaluates the deterministic check suite — service liveness, mTLS expiry, SLO burn, the money/audit/
kill-switch invariants, and per-business health (reusing ab_obs) — and emits them in the Nagios
plugin protocol. A real submit adapter (Icinga2 REST) slots in behind the NagiosExporter port
(see `python -m ab_monitor.submit`).
"""

from __future__ import annotations

from ab_monitor.exporter import StubNagiosExporter, render_all
from ab_monitor.suite import demo_suite


def main() -> int:
    results = demo_suite()
    print(render_all(results))
    StubNagiosExporter().export(results)  # a real adapter would submit these to Nagios/Icinga2
    crit = sum(1 for r in results if r.status.name == "CRITICAL")
    warn = sum(1 for r in results if r.status.name == "WARNING")
    print(f"\n  {len(results)} checks: {crit} CRITICAL, {warn} WARNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
