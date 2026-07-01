# M2 — Invariant checks (money / audit / kill-switch)

**Parent:** PRD 0005 / ADR-0055. **Triage:** ready-for-agent.

## What to build

The checks that surface the skeleton's hard invariants as CRITICAL when broken — the things that
must page immediately. Pure evaluators over injected signals:
- **Ledger balance**: `trial_balance() != 0` → CRITICAL (money corruption); perfdata `trial_balance=0`.
- **Audit hash-chain integrity**: a broken chain → CRITICAL; perfdata on entries verified.
- **Kill-switch status**: active → CRITICAL/WARNING with the scope + reason in the output (the halt
  state must be visible), clear → OK.

Register them in the `ab_monitor` check registry so `make monitor` includes them.

## Acceptance criteria

- [ ] Ledger-balance evaluator: zero → OK, non-zero → CRITICAL with the imbalance in the output.
- [ ] Audit-integrity evaluator: intact chain → OK, break → CRITICAL.
- [ ] Kill-switch evaluator: clear → OK; active → CRITICAL/WARNING carrying scope + reason.
- [ ] Each evaluator is a pure function over an injected signal (no infra), unit-tested with
      independent literals; included in `make monitor`. ruff + mypy strict clean.

## Blocked by

- M1 (the `CheckResult` model + registry + exporter).
