# 02 — Persisted provisioning + capital allocation

Status: todo
PRD: docs/prd/0002-business-factory.md  ·  Triage: ready-for-agent  ·  Blocked by: 01

## What to build (Seam 2 — integration vs Postgres + ledger + bus)

`ab_factory.store`: persist businesses and run the real provision flow, allocating capital
through the ledger and publishing the activation event.

- Postgres `businesses` table (business_id PK, name, status, capital_minor, created_at) in db._DDL.
- `provision(blueprint, capital_minor)`: reject-underfunded → persist `draft` → allocate capital
  (`ab_ledger.store.post`: debit `<business_id>:cash` / credit `portfolio:treasury`) → readiness
  (real signals: `<business_id>:cash` balance, `ab_killswitch` state, `ab_compliance.ropa.check()`)
  → `active` (publish `BusinessActivated` on the bus) else stays `draft` (capital locked).
- `get`/`list` businesses; a `businesses`-truncating test fixture.

## Acceptance criteria

- [ ] After provisioning a funded, clean business: row is `active`; `<business_id>:cash` == capital;
      `ledger.trial_balance() == 0`; exactly one `BusinessActivated` on the bus.
- [ ] A business blocked by kill-switch or RoPA stays `draft` with capital allocated (locked); no event.
- [ ] Underfunded provision writes nothing.
- [ ] Integration tests against `make up-infra` (prior art: ab_ledger.store, test_payments.py). ruff + mypy clean.

## Blocked by
01 (Factory core + demo).
