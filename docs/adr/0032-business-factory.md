---
status: accepted
---

# Business Factory — instantiate a business from a Blueprint + capital

Planned with the project's spec-driven skills (grill → PRD 0002 → to-issues → tdd), acting on
the recommendations' **P1 Multi-Business** and the **P0 `business_id`** seam. Turns a
`Blueprint` + capital into a live, funded, launch-gated business, so the platform can run
*many* businesses side by side instead of one.

## Decisions (from the grilling session)

- **Logical multi-tenancy via `business_id`.** Ledger accounts scoped by the existing prefix
  convention: `<business_id>:cash`, shared `portfolio:treasury`. No physical (schema/topic)
  isolation — documented as a later hardening.
- **Capital is real double-entry ledger money.** Allocation books debit `<business_id>:cash` /
  credit `portfolio:treasury` (treasury unbounded → its balance = total capital deployed);
  `trial_balance()==0` holds. `Blueprint.experiment_budget_minor` stays the per-experiment
  sub-cap (growth engine); the Factory's `capital_minor` is total runway (≥ experiment budget).
- **Lifecycle `draft → active → sunset`**, in a persisted `businesses` registry.
  `provision()`: reject underfunded (nothing written) → register `draft` → allocate capital →
  run readiness → `active` if ready, else `draft` with capital **locked**.
- **Readiness is a real launch gate** (architecture/16: "no venture launches until audits
  pass"): pure `readiness(business, *, cash_balance, kill_switch_clear, compliance_clear)` —
  capital funded, kill-switch clear, compliance (RoPA) clear — the store wires the real signals.
- **`can_spend` = active + positive + within remaining cash** (pure). Wiring it into
  `payments.transfer` is the explicit next slice (Half 2).
- **`BusinessActivated` event** (business-scoped) published on activation for a future portfolio
  context.
- **`ab_factory` = pure `core` + Postgres `store`** (same split as `ab_ledger`); `make factory`
  is an infra-free CI gate.

## Verified (Slice 1 — core + demo)

- TDD, one test at a time: 9 pure `ab_factory.core` tests — provision (funded → draft),
  underfunded rejected, readiness ready/blocked-with-reasons, activate ready-gated + re-check
  after a blocker clears, `can_spend` allow + three deny paths, `BusinessActivated` fields.
  `make factory` provisions two businesses (one `active` + spendable, one blocked-`draft` on
  compliance) and refuses an underfunded provision. lint + mypy strict clean.

## Verified (Slice 2 — persisted `store`)

- Integration vs `make up-infra` (3 tests): a funded, clean business is provisioned →
  **`active`**, its capital is real ledger money (`<business_id>:cash == capital`,
  `trial_balance()==0`), and exactly one `BusinessActivated` lands on the bus; a business under
  an active kill-switch stays **`draft`** with capital allocated-but-locked (no event); an
  underfunded provision writes nothing. Capital allocation is a maker-checker ledger txn
  (portfolio agent + treasury control). `businesses` table stores the blueprint as jsonb so
  `get()` rehydrates a full `Business`.
- Fixed a latent pytest import collision (duplicate `test_core.py`/`test_store.py` basenames
  across `tests/` dirs with no `__init__.py`) by using unique basenames.

## Verified (Half 2 — enforced business-scoped payments)

- `PaymentTransfer` gains an optional `business_id`. When set, `transfer_payment` gates the
  payment through the Factory *before* the ledger: fetch the business (unknown → `ToolDenied`
  400), **live** `readiness()` (kill-switch / RoPA / funded re-checked at spend time), then
  `can_spend()` (runway) — either failing → `ToolDenied` 403; the debit is scoped to
  `<business_id>:cash`, and the ledger's cap / maker-checker / payee-allow-list / idempotency
  still apply on top (two independent gates).
- Integration vs `make up-infra` (5 tests): an active business's payment debits its own cash
  (`external:<payee>` up, `<business_id>:cash` down, `trial_balance()==0`); a kill-switched
  business is blocked "not launch-ready" (nothing spent); an over-runway payment is blocked
  ("insufficient runway"); an unknown business is denied; **a payment without `business_id` is
  unchanged** (backward compatible). Full gateway suite 40 green. lint + mypy strict clean.

## Deferred

A portfolio capital cap (bounded treasury), a portfolio analytics/allocation layer, and
`business_id` propagation through the existing contexts' events/DB. See PRD 0002 "Out of Scope".
