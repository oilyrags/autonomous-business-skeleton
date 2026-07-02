"""Invariant checks (pure): the skeleton's hard guarantees surfaced as CRITICAL when broken — the
things that must page immediately. Each evaluator takes an injected signal (the caller reads the
real ledger / audit chain / kill-switch state), so the logic stays infra-free and testable.
"""

from __future__ import annotations

from ab_monitor.check import CheckResult, CheckStatus, Perfdatum


def ledger_balance_check(*, trial_balance: int) -> CheckResult:
    """The double-entry invariant: the ledger's signed entries must sum to zero. Non-zero = money
    corruption → CRITICAL."""
    perf = (Perfdatum("trial_balance", trial_balance, warn=0, crit=0),)
    if trial_balance == 0:
        return CheckResult("ledger-balance", CheckStatus.OK, "trial balance is zero", perf)
    return CheckResult(
        "ledger-balance", CheckStatus.CRITICAL, f"trial balance is {trial_balance}, not zero", perf
    )


def audit_integrity_check(*, intact: bool, entries_verified: int) -> CheckResult:
    """The audit hash-chain must verify end to end. A break = tampering/corruption → CRITICAL."""
    perf = (Perfdatum("entries_verified", entries_verified),)
    if intact:
        return CheckResult(
            "audit-integrity", CheckStatus.OK, f"hash chain intact ({entries_verified} entries)", perf
        )
    return CheckResult("audit-integrity", CheckStatus.CRITICAL, "audit hash chain broken", perf)


def kill_switch_check(*, active: bool, scope: str | None = None, reason: str | None = None) -> CheckResult:
    """The halt state must be visible. Active = agents are stopped → CRITICAL, carrying scope+reason."""
    if not active:
        return CheckResult("kill-switch", CheckStatus.OK, "kill switch clear")
    detail = f"kill switch ACTIVE (scope={scope or 'global'}; reason={reason or 'unspecified'})"
    return CheckResult("kill-switch", CheckStatus.CRITICAL, detail)
