---
status: accepted
---

# Finance context: deterministic double-entry ledger — Audit 7

The sharpest expression of the project's core doctrine — *deterministic systems do money;
never LLM math on financial paths*. A new `ab_ledger` (Finance) context closes verification
Audit 7's three build-time criteria: the ledger-balance invariant, double-payment
failure-injection, and maker-checker enforced in the workflow (architecture/03, 06 AM-09..13).

## Decisions

- **Money is integer minor units, never a float.** Exact, reproducible arithmetic.
- **Double-entry.** A `Transaction` is signed `Posting`s (+ debit, − credit) that MUST sum to
  zero; `validate()` rejects an unbalanced or empty transaction before anything is written.
  The whole ledger therefore always sums to zero — `trial_balance() == 0` is the **balance
  invariant**.
- **Idempotency = no double-payment.** Each transaction carries an `idempotency_key`. The
  in-memory ledger skips a repeat key; the Postgres store enforces it at the database — the
  header's `idempotency_key` is UNIQUE, inserted `ON CONFLICT DO NOTHING RETURNING`; a
  replayed payment lands zero rows and posts nothing, atomically.
- **Maker-checker + separation of duties.** A payment whose magnitude exceeds
  `PAYMENT_CAP_MINOR` (env-overridable) requires a `checker` distinct from the `maker`;
  `validate()` raises `ApprovalRequired` (no checker) or `SeparationOfDutiesViolation`
  (checker == maker). Enforced before any write.
- **Pure core + thin persistence.** `core.py` (primitives, `validate`, `InMemoryLedger`) is
  deterministic and infra-free — where the invariants live and are proven. `store.py` mirrors
  it on Postgres (append-only `ledger_txns` + `ledger_entries`). `make ledger` runs the
  in-memory self-check in CI with no infra.

## Verified

- Infra-free (`ab_ledger/tests/test_core.py`, 9) + `make ledger`: balanced valid / unbalanced
  + empty rejected; invariant `trial_balance()==0` with correct per-account balances; a
  replayed idempotency key is a no-op (balance not doubled); over-cap needs a checker;
  checker≠maker (SoD); a distinct-checker payment is valid; under-cap needs no checker.
- Integration (`test_store.py`, 4, against `make up-infra`): the invariant holds in Postgres;
  a re-submitted payment (same key) **posts nothing** (double-payment injection); maker-checker
  is enforced before persistence (nothing written); an approved payment persists. lint + mypy
  strict clean.

## Audit impact

**Audit 7 (finance) → PASS (build-proven).** `architecture/16` updated; CONDITIONAL 3 → 2
(remaining: 4 compliance-CI, 12 failure-injection).

## Deferred

Wiring a `payments.transfer` tool through the gateway to the ledger (with the tool registry's
egress + maker-checker gates); payment allow-lists / per-payee caps; multi-currency and FX;
the ledger as a service + `LedgerEntryPosted` events; period close / reconciliation reports.
