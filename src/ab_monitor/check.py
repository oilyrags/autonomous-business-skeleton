"""Monitoring checks (pure, deterministic): evaluate a signal against thresholds into a Nagios
plugin CheckResult (status + output + perfdata). No signal is invented here — evaluators reuse the
skeleton's existing signals (service health, mTLS expiry, `ab_ops` error budget). The vendor-neutral
plugin protocol means Nagios Core, Icinga2, and Naemon all consume the results unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum

from ab_ops.reliability import ErrorBudget


class CheckStatus(IntEnum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


@dataclass(frozen=True)
class Perfdatum:
    """One machine-readable metric on a check: ``label=value;warn;crit`` (Nagios perfdata)."""

    label: str
    value: float
    warn: float | None = None
    crit: float | None = None

    def render(self) -> str:
        return f"{self.label}={_num(self.value)};{_opt(self.warn)};{_opt(self.crit)}"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    output: str
    perfdata: tuple[Perfdatum, ...] = ()
    business_id: str | None = None  # set for per-business checks (multi-tenancy)

    def render(self) -> str:
        """Render the classic Nagios plugin line: ``STATUS: output | perfdata``."""
        line = f"{self.status.name}: {self.output}"
        if self.perfdata:
            line += " | " + " ".join(p.render() for p in self.perfdata)
        return line


@dataclass(frozen=True)
class Check:
    """A named check: a thunk that produces a result when run (the registry unit)."""

    name: str
    run: Callable[[], CheckResult]
    tags: tuple[str, ...] = field(default_factory=tuple)


def run_all(checks: list[Check]) -> list[CheckResult]:
    """Run every registered check, in order."""
    return [c.run() for c in checks]


# --- Evaluators (pure; reuse existing signals) --------------------------------------------------


def service_check(service: str, *, healthy: bool) -> CheckResult:
    """Liveness from a service's `/health` probe result."""
    if healthy:
        return CheckResult(f"{service}-up", CheckStatus.OK, f"{service} responding")
    return CheckResult(f"{service}-up", CheckStatus.CRITICAL, f"{service} not responding")


def cert_expiry_check(service: str, *, days_remaining: int, warn_days: int, crit_days: int) -> CheckResult:
    """mTLS certificate expiry — a lapsed cert breaks the mesh, so warn early, crit late."""
    perf = (Perfdatum("days", days_remaining, warn_days, crit_days),)
    if days_remaining <= crit_days:
        status = CheckStatus.CRITICAL
    elif days_remaining <= warn_days:
        status = CheckStatus.WARNING
    else:
        status = CheckStatus.OK
    return CheckResult(f"{service}-mtls-cert", status, f"cert expires in {days_remaining} days", perf)


def slo_burn_check(service: str, budget: ErrorBudget, errors: int, *, warn_ratio: float = 0.9) -> CheckResult:
    """SLO error-budget burn (reuses `ab_ops.ErrorBudget`) — alert on budget burn, not raw thresholds."""
    perf = (Perfdatum("errors", errors, round(warn_ratio * budget.budget), budget.budget),)
    if budget.exhausted(errors):
        status = CheckStatus.CRITICAL
        output = f"{service} error budget exhausted ({errors}/{budget.budget})"
    elif errors >= warn_ratio * budget.budget:
        status = CheckStatus.WARNING
        output = f"{service} error budget {errors}/{budget.budget} burned"
    else:
        status = CheckStatus.OK
        output = f"{service} within error budget ({errors}/{budget.budget})"
    return CheckResult(f"{service}-slo-burn", status, output, perf)


def _num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _opt(value: float | None) -> str:
    return "" if value is None else _num(value)
