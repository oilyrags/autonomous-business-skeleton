"""The Nagios exporter port: renders/submits check results in the plugin protocol. The stub records
+ renders (no infra); a real adapter submits via NSCA / check_mrpe (Nagios) or the Icinga2
process-check-result REST API — callers never change. This is the seam monitoring.md's integration
plugs into.
"""

from __future__ import annotations

from typing import Protocol

from ab_monitor.check import CheckResult


def render_all(results: list[CheckResult]) -> str:
    """Render a suite as newline-separated Nagios plugin lines (what a passive check submits)."""
    return "\n".join(r.render() for r in results)


class NagiosExporter(Protocol):
    """Submit check results to a monitoring system."""

    def export(self, results: list[CheckResult]) -> None: ...


class StubNagiosExporter:
    """Deterministic exporter for tests + the demo: records what would be submitted, no network. A
    real NSCA / Icinga2-REST adapter implements the same ``export``."""

    def __init__(self) -> None:
        self.submitted: list[CheckResult] = []

    def export(self, results: list[CheckResult]) -> None:
        self.submitted.extend(results)
