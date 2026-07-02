"""Invariant checks: ledger balance, audit integrity, kill-switch (pure, infra-free)."""

from __future__ import annotations

from ab_monitor.check import CheckStatus
from ab_monitor.invariants import audit_integrity_check, kill_switch_check, ledger_balance_check


def test_ledger_balance_ok_at_zero_critical_otherwise() -> None:
    assert ledger_balance_check(trial_balance=0).status is CheckStatus.OK
    bad = ledger_balance_check(trial_balance=500)
    assert bad.status is CheckStatus.CRITICAL and "500" in bad.output


def test_audit_integrity_ok_when_intact_critical_on_break() -> None:
    assert audit_integrity_check(intact=True, entries_verified=1200).status is CheckStatus.OK
    broken = audit_integrity_check(intact=False, entries_verified=1200)
    assert broken.status is CheckStatus.CRITICAL and "broken" in broken.output


def test_kill_switch_ok_when_clear_critical_with_context_when_active() -> None:
    assert kill_switch_check(active=False).status is CheckStatus.OK
    fired = kill_switch_check(active=True, scope="agent", reason="anomaly")
    assert fired.status is CheckStatus.CRITICAL
    assert "agent" in fired.output and "anomaly" in fired.output


def test_invariant_results_render_as_nagios_lines() -> None:
    assert ledger_balance_check(trial_balance=0).render() == "OK: trial balance is zero | trial_balance=0;0;0"
