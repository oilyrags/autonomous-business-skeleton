"""ab_ledger — the Finance context: a deterministic double-entry ledger.

Money math is deterministic code, never model output (architecture/03, 06 AM-09..13):
append-only, double-entry (every transaction balances), idempotent (no double-payment),
and maker-checker + separation-of-duties for payments above the cap.
"""
