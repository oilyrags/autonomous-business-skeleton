---
status: accepted
---

# Property-based tests for the money-critical invariants

The ledger and the portfolio allocator are the two places that move money, and their guarantees are
*universal* ("the books always balance", "capital is never over-deployed"), not example-shaped. The
example-based unit tests pin specific cases; these add **property-based tests** (Hypothesis) that
assert the invariants hold for arbitrary inputs, so a regression that only shows up on an unusual
portfolio or transaction sequence is caught. Acting on the recommendations' P4 (property-based
tests).

## Decisions

- **`hypothesis>=6` in the `dev` group** (synced in CI via `uv sync --frozen`; the lock is updated).
- **Pure, infra-free** — both suites exercise `InMemoryLedger` and the pure `allocate`, so they run
  in the standard CI test step with no infra, alongside the rest of the fast suite.
- **Generators stay inside the rules under test.** Ledger transfers use internal accounts only
  (no `external:` prefix) and magnitudes ≤ the cap, so every generated transfer is auto-approvable —
  the suite exercises the *balance* invariant, not the approval rules (which have their own tests).

## Invariants pinned

**Ledger** (`src/ab_ledger/tests/test_ledger_properties.py`): for any sequence of balanced
transfers — `trial_balance() == 0`; the account balances sum to zero; and replaying one
`idempotency_key` N times moves money exactly once (first post applies, every replay is a no-op).

**Allocator** (`src/ab_portfolio/tests/test_portfolio_properties.py`): for any portfolio, budget and
increment — every business gets exactly one recommendation in input order; a SUNSET reclaims exactly
that business's capital; **new capital deployed never exceeds the budget headroom left after sunsets**
(`invested ≤ max(0, budget − (deployed − reclaimed))`, and net stays ≤ budget when it started within
it); and only INVEST_MORE / SUNSET carry a non-zero `capital_delta` (INVEST_MORE always exactly one
increment).

## Verified

7 property tests (3 ledger + 4 allocator). Full suite 138 passed, 33 skipped; ruff + mypy strict
clean (80 files); `uv sync --frozen` consistent.
