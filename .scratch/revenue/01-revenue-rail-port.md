# Slice 50 — ab_revenue: revenue rail port + stub + ledger booking

**Parent:** PRD 0003. **Why.** The econ loop's revenue is still injected. A business must be able to
*receive money from customers* and have it booked to the ledger per business, so profitability runs
on real income. Follows the model-provider port pattern (stub default, real Stripe/Lemon Squeezy
adapter behind the same interface).

## What to build

A new `ab_revenue` context: a `RevenueGateway` **port** (Protocol) with a `StubRevenueGateway`
default that yields settled `Charge`s; a pure `to_transaction(charge, *, maker)` that books a
balanced ledger revenue posting (`{business_id}:cash` +amount / `{business_id}:revenue` −amount, so
money is conserved and the trial balance stays 0); a `RevenueReceived` domain event
(business-scoped, financial); a `record_charges(gateway, ledger, *, maker)` orchestration that books
each charge and returns the events; and a ledger `business_revenue(business_id)` read
(`−account_balance({bid}:revenue)`) on both `InMemoryLedger` and the Postgres `store`, mirroring
`business_spend`. `make revenue` demo (infra-free) + CI step.

## Acceptance criteria

- [ ] `Charge` (business_id, amount_minor≥0, currency, customer_ref, external_ref) + pure
      `to_transaction` producing a balanced posting; `trial_balance()==0` after posting.
- [ ] `RevenueReceived` event added to `ab_schemas` + `events.asyncapi.yaml`; the AsyncAPI contract
      test passes (drives the spec addition).
- [ ] `RevenueGateway` Protocol + `StubRevenueGateway` returning configured charges; a real adapter
      would slot in behind the same interface.
- [ ] `ledger.business_revenue(business_id)` on `InMemoryLedger` (pure) and Postgres `store`.
- [ ] `record_charges` books each charge and emits one `RevenueReceived` per charge, business-scoped.
- [ ] `make revenue` (in CI) demos two businesses receiving revenue; ruff + mypy strict clean.

## Blocked by

None — can start immediately.
