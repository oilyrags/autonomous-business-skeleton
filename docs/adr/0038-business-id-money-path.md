---
status: accepted
---

# Propagate business_id through the money path

The portfolio/econ pipeline attributes outcomes per `business_id`, but the **ledger** — where money
actually moves — did not record which business a payment belonged to. Downstream could only infer it
by parsing `{business_id}:cash` account-name strings. This threads `business_id` through the ledger
transaction, its persisted row, and the published `LedgerEntryPosted` event, so every money movement
is first-class attributable. Recommendations P4 (business_id propagation); scope is the money path —
the `decisions` / `AgentDecisionMade` path is the next slice.

## Changes

- **`LedgerEntryPosted.business_id: str | None`** (optional — a platform/treasury payment has no
  business). The **contract test drove this**: adding the field failed field-parity until the
  AsyncAPI `LedgerEntryPosted` payload gained an optional `businessId` (not `required`) — exactly the
  drift guard from ADR-0037 doing its job.
- **`Transaction.business_id: str | None`** (core dataclass) — carried on the txn; pure, so
  `InMemoryLedger` and validation are unaffected (`magnitude`/`payees` unchanged).
- **Persisted**: `ledger_txns.business_id text` (nullable; added to the `IF NOT EXISTS` DDL) and
  `store.post` writes it.
- **Propagated at the gateway**: `transfer_payment` sets `business_id` on both the `Transaction` and
  the `LedgerEntryPosted`; `complete_for_business`'s LLM-metering txn sets it too — so metered
  inference spend is attributable to its business as well.

## Verified

- Pure: `LedgerEntryPosted` business_id defaults None and round-trips as camelCase `businessId`;
  contract parity holds (24 contract tests green).
- Integration (skips without infra): a business-scoped payment persists `business_id` on the
  `ledger_txns` row and publishes `LedgerEntryPosted` with the right `businessId`.
- Full suite 164 passed, 34 skipped; ruff + mypy strict clean (80 files).

## Deferred

`business_id` on `decisions` / `AgentDecisionMade`; a `ledger_store.business_spend(business_id)`
query so econ can source real per-business spend from the ledger instead of injected inputs.
