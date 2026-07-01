# Slice 48 — Source per-business spend from the ledger (wire ab_econ to real money)

**Why.** `ab_econ` today takes fully-injected `UnitInputs`, including the spend side. But the spend
already happened and is recorded in the ledger (LLM metering + business-scoped external payments,
both now carrying `business_id` after slice 47). Derive the spend from the ledger instead of handing
it to econ, so unit economics reflect what actually happened. Revenue/customers stay injected (no
revenue rail yet). Recommendations P3/P4.

**Decisions.**
1. **`business_spend(business_id) -> LedgerSpend`** on both ledgers (the pure `InMemoryLedger` method
   and the Postgres `store` function), mirroring the existing `account_balance`/`trial_balance` pair.
   `LedgerSpend(business_id, llm_spend_minor, external_spend_minor)` — a pure `ab_ledger.core` type.
   - `llm_spend_minor` = balance of the `{business_id}:llm_spend` cost account (from the gateway's
     metering txns).
   - `external_spend_minor` = money the business paid to outside parties = sum of positive
     `external:*` postings across ledger transactions whose `business_id` matches (ad/supplier spend).
2. **`InMemoryLedger` tracks applied transactions** (`_txns`) so `external_spend` can be attributed
   per business — postings alone don't carry `business_id`; the transaction header does. Pure, no I/O.
3. **`ab_econ` stays pure/decoupled** — no ledger import. The caller assembles
   `UnitInputs(..., ad_spend_minor=spend.external_spend_minor, llm_spend_minor=spend.llm_spend_minor)`
   from `LedgerSpend` + injected `revenue_minor`/`cogs_minor`/`customers`.

**Behaviors to test.**
- Pure (`InMemoryLedger`): after an LLM-metering txn + a business-scoped external payment,
  `business_spend(bid)` returns the right llm/external split; another business's spend is isolated;
  a business with no activity → zeros. Feeding it into `UnitInputs` yields the expected `economics`.
- Integration (`store`, skips without infra): same, against Postgres via the `business_id` column.

ruff + mypy-strict clean; unique test basenames.
