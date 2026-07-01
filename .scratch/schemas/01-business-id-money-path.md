# Slice 47 — Propagate business_id through the money path

**Why.** The portfolio/econ pipeline attributes outcomes per `business_id`, but the **ledger** —
where the money actually moves — doesn't record which business a payment belongs to. Downstream can
only guess by parsing `{business_id}:cash` account-name strings. Thread `business_id` through the
ledger transaction, its persisted row, and the published `LedgerEntryPosted` event so every money
movement is first-class attributable. Recommendations P4 (business_id propagation). Scope: the money
path only; the `decisions`/`AgentDecisionMade` path is the next slice.

**Decisions.**
1. **`LedgerEntryPosted.business_id: str | None = None`** (optional — a platform/treasury payment
   has no business). The **contract test drives this**: adding the field fails field-parity until the
   AsyncAPI `LedgerEntryPosted` payload gains an optional `businessId` (not in `required`).
2. **`Transaction.business_id: str | None = None`** (core dataclass) — carried on the txn; pure, so
   `InMemoryLedger` keeps working unchanged. Does not affect `magnitude`/`payees`/validation.
3. **Persist it**: `ledger_txns.business_id text` (nullable; added to the `IF NOT EXISTS` DDL — fresh
   CI/dev DBs get it) and `store.post` writes it.
4. **Propagate at the gateway**: `transfer_payment` sets `business_id=p.business_id` on both the
   `Transaction` and the `LedgerEntryPosted`; `complete_for_business`'s metering txn sets it too.

**Behaviors to test.**
- Event (pure): `LedgerEntryPosted` with `business_id` round-trips as `businessId` (camelCase wire).
- Contract (pure, existing suite): parity holds after the spec update; `businessId` optional.
- Core (pure): a `Transaction` carries `business_id`; default None; balance/validation unaffected.
- Wiring (integration, skips without infra): a business-scoped payment publishes `LedgerEntryPosted`
  with the right `businessId` and persists it on the `ledger_txns` row; a non-business payment → None.

ruff + mypy-strict clean; unique test basenames.
