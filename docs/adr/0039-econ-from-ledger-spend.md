---
status: accepted
---

# Source per-business spend from the ledger

`ab_econ` took fully-injected `UnitInputs`, including the spend side — but the spend already happened
and is recorded in the ledger (LLM metering + business-scoped external payments, both attributable
by `business_id` since ADR-0038). This adds a `business_spend` query so unit economics reflect what
actually happened, instead of numbers handed to econ. Revenue/customers stay injected (no revenue
rail yet). Recommendations P3/P4.

## Decisions

- **`business_spend(business_id) -> LedgerSpend`** on both ledgers — the pure `InMemoryLedger` method
  and the Postgres `store` function — mirroring the existing `account_balance` / `trial_balance`
  pair. `LedgerSpend(business_id, llm_spend_minor, external_spend_minor)` is a pure `ab_ledger.core`
  type:
  - `llm_spend_minor` = balance of the `{business_id}:llm_spend` cost account (gateway metering).
  - `external_spend_minor` = money paid to outsiders = sum of positive `external:*` postings across
    transactions whose `business_id` matches (ad / supplier spend).
- **`InMemoryLedger` now tracks applied transactions** (`_txns`), because postings alone don't carry
  `business_id` — the transaction header does. Still pure, no I/O; a natural fit that also makes the
  Postgres query test-mirrored in CI.
- **`ab_econ` stays pure and ledger-free.** The caller assembles
  `UnitInputs(..., ad_spend_minor=spend.external_spend_minor, llm_spend_minor=spend.llm_spend_minor)`
  from `LedgerSpend` + injected `revenue_minor`/`cogs_minor`/`customers`. No new coupling.

## Verified

- Pure (`InMemoryLedger`): the llm/external split; per-business isolation; zero spend for an inactive
  business; and a `LedgerSpend` → `UnitInputs` → `economics` round-trip yielding the expected profit,
  verdict and CAC. 4 tests.
- Integration (`store`, skips fast without infra): the same split derived from Postgres via the
  `business_id` column; zero for no activity. 2 tests.
- Full suite 168 passed, 36 skipped; ruff + mypy strict clean (80 files).

## Deferred

A revenue rail so revenue/cogs/customers are also ledger/rail-sourced (closing the last synthetic
seam); folding the ledger-derived economics verdict into the portfolio's `unprofitable_business_ids`
so allocation runs on real money end to end.
