# 01 — Business Factory core + demo

Status: done (2026-07-01) — 9 pure tests, make factory in CI
PRD: docs/prd/0002-business-factory.md  ·  Triage: ready-for-agent  ·  Blocked by: none

## What to build (Seam 1 — pure, infra-free)

The `ab_factory.core` decision logic that instantiates and gates a business, plus the
`BusinessActivated` event contract and a `make factory` demo. No I/O — signals are injected.

- `Business` (business_id, name, capital_minor, status) + status lifecycle `draft → active → sunset`.
- A pure registry (in-memory) supporting register/get/list.
- `provision(blueprint, capital_minor)` logic: reject if `capital_minor < experiment_budget_minor`
  (nothing created); else register `draft`. (Capital allocation + activation are driven by the
  caller/store; the core exposes the state transitions.)
- `readiness(business, *, cash_balance, kill_switch_clear, compliance_clear) -> Readiness(ready, reasons)`
  — 3 checks: capital funded (`cash_balance >= experiment_budget`), kill-switch clear, compliance clear.
- `activate(business, readiness)` — flips `draft → active` only if ready; else stays `draft`.
- `can_spend(business, amount_minor, *, cash_balance) -> (allowed, reason)` — active + positive + within cash.
- `BusinessActivated(business_id, name, capital_minor)` added to `ab_schemas.events` (internal).
- `make factory` (in CI): infra-free demo across ≥2 businesses hitting active + blocked paths.

## Acceptance criteria

- [ ] Underfunded provision (`capital < experiment_budget`) is rejected; nothing registered.
- [ ] A business reaches `active` iff all three readiness checks pass; otherwise stays `draft` with reasons.
- [ ] Re-running readiness after a blocked condition clears activates the business.
- [ ] `can_spend` allows on active+funds; denies on not-active, non-positive, or amount > cash.
- [ ] `BusinessActivated` event carries business_id/name/capital_minor.
- [ ] `make factory` runs infra-free and shows active + blocked across ≥2 businesses; green in CI.
- [ ] ruff + mypy-strict clean; pure tests cover every branch (prior art: ab_ledger.core, ab_ops).

## Blocked by
None.
