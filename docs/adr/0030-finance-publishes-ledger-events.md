---
status: accepted
---

# Finance publishes LedgerEntryPosted — the money path becomes eventful

The `payments.transfer` path moved money and audited it, but the Finance context did not
publish a domain event. Per the DDD doctrine (contexts integrate via published events, not by
reading each other's stores), a successful payment now emits `LedgerEntryPosted` on the bus.

## Decisions

- **`LedgerEntryPosted`** (financial-classified, `ab_schemas.events`) carries txn_id,
  idempotency_key, amount_minor, currency, payee, maker, checker — enough for a downstream
  consumer (analytics/reconciliation) without touching the ledger's private store.
- **Emitted once per applied transaction, never on a replay.** `store.post` returns whether the
  transaction was newly applied; `transfer_payment` publishes only when it was, so an idempotent
  retry moves no money *and* produces no duplicate event.
- **Published on `finance.ledger.posted`** (`settings.ledger_topic`); the gateway ensures the
  topic at startup, matching the decision-topic pattern.

## Verified

- Integration (`test_payments.py`): a duplicate payment posts once, and a fresh consumer reads
  exactly one `LedgerEntryPosted` for that idempotency key (`amountMinor` correct) — none for the
  replay. Full payments + happy-path suites green. lint + mypy strict clean.

## Deferred

A Finance data product / medallion consuming `LedgerEntryPosted` into financial KPIs — the
pattern is already proven by the decisions medallion (`ab_data`); replicating it per domain is
per-venture instantiation work, not skeleton work.
