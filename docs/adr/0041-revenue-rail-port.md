---
status: accepted
---

# Revenue rail: port + stub + ledger booking

Closes the P0 "integrate real payment rails" gap and removes the revenue side's synthetic-input
status. A business can now *receive money from customers* and have it booked to the ledger per
business. Part of PRD 0003 (close-recommendation-gaps), spec-driven (issue → tdd).

## Decisions

- **New `ab_revenue` context** with the model-provider seam pattern: a `RevenueGateway` **port**
  (`Protocol`, `settled_charges() -> list[Charge]`) + a `StubRevenueGateway` default. A real
  Stripe/Lemon Squeezy adapter implements the same port; callers never change.
- **`Charge`** (business_id, amount_minor≥0, currency, customer_ref, external_ref). `external_ref` is
  the rail's charge id — the **idempotency anchor** (`idempotency_key = rev_<external_ref>`), so a
  replayed charge books nothing.
- **Booking through the double-entry ledger**: `to_transaction` debits `{business_id}:cash` (+),
  credits `{business_id}:revenue` (−). Money conserved, `trial_balance() == 0`.
- **Inbound revenue is exempt from the outbound payment cap**: it has no `external:` payee, so
  maker-checker / cap / allow-list (which gate money *leaving* to a payee) don't apply — the spend
  path still enforces all of them on the way out, so inflated cash can't bypass outbound controls.
  `record_charges` posts with `cap = max(PAYMENT_CAP_MINOR, amount)`.
- **`RevenueReceived`** event (business-scoped, financial) — added to `ab_schemas` +
  `events.asyncapi.yaml`; the ADR-0037 contract test drove the spec addition.
- **`ledger.business_revenue(business_id)`** on both `InMemoryLedger` and the Postgres `store`
  (`−account_balance({bid}:revenue)`), mirroring `business_spend` — the read `ab_econ` will consume.

## Verified

4 pure tests (balanced booking + `business_revenue` + cash + trial balance; charge → event; multi-
charge multi-business; idempotent on `external_ref`); AsyncAPI contract green (+3). `make revenue`
(in CI) books two businesses' charges to the ledger. Full suite 178 passed, 36 skipped; ruff + mypy
strict clean (85 files).

## Deferred

Real Stripe/Lemon Squeezy adapter (webhook verification, settlement); `ab_econ` consuming
`business_revenue` so the closed loop runs on real revenue (next slice); refunds/chargebacks.
