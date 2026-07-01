# PRD 0002 — Business Factory (instantiation, capital, readiness)

> **Triage label:** `ready-for-agent`
> **Status:** drafted, pending publish to GitHub Issues (the configured tracker; requires `gh`, not yet installed — see Further Notes).
> **Source:** grilling session, 2026-07-01 (10 resolved decisions). Acts on `~/Downloads/recommendations.md` **P1 Multi-Business & Portfolio Management** and the **P0** cross-cutting `business_id` seam. Related: ADR-0031 (`ab_growth` / `Blueprint`), ADR-0023/0026/0030 (`ab_ledger`), architecture/14 (instantiation), 06 (autonomy/launch gates), 16 §"no venture launches until audits pass".

## Problem Statement

The skeleton runs **one** high-trust AI business well, but there is no first-class way to *instantiate* a new business: allocate it real capital, isolate its money and identity from other businesses, and refuse to let it spend until it is actually fit to launch. Today `ab_growth.Blueprint` describes a business on paper, yet nothing turns a blueprint + capital into a live, funded, launch-gated business — and there is no `business_id` seam to keep many businesses apart. Without this, "run numerous businesses" is impossible and multi-tenancy would have to be retrofitted painfully later.

## Solution

A **Business Factory**: from a `Blueprint` + an initial capital amount, it registers a business, books that capital into the shared ledger under a per-business namespace, and runs a **readiness gate** (a real launch blocker) that a business must pass before it becomes `active` and may spend. Every business gets a `business_id` that scopes its ledger accounts (`<business_id>:cash`) and its lifecycle events, so many businesses run side by side on one trust-and-money core. Capital that a business holds is real money in the audited double-entry ledger, not a side-field; a business that fails the gate keeps its capital *locked* until it clears. The Factory also answers "can this business spend `X`?" as a pure, testable decision that a later slice will wire into the payment path.

## User Stories

1. As a portfolio operator, I want to instantiate a new business from a blueprint plus an initial capital amount, so that launching a business is one governed step, not bespoke setup.
2. As a portfolio operator, I want each business to have a unique `business_id`, so that its money, identity, and events are kept separate from every other business.
3. As a finance owner, I want a business's initial capital booked into the shared ledger as a real double-entry transaction, so that capital is audited, invariant-checked money — not an untracked number.
4. As a finance owner, I want a business's capital debited to `<business_id>:cash` and credited to `portfolio:treasury`, so that a business has a real spendable balance and the portfolio's total deployed capital is visible.
5. As a finance owner, I want the global ledger balance invariant to still hold after capital allocation, so that provisioning can never corrupt the books.
6. As a portfolio operator, I want provisioning a business whose capital is below its experiment budget to be rejected outright with nothing written, so that under-funded businesses never enter the registry.
7. As a portfolio operator, I want a newly registered business to start in a `draft` state, so that it cannot act before it is cleared.
8. As a governance owner, I want a business to become `active` only after passing a readiness gate, so that launch is a real control, not a formality.
9. As a governance owner, I want the readiness gate to require the business to be capitally funded (its `<business_id>:cash` at least its experiment budget), so that it cannot launch without runway.
10. As a security owner, I want the readiness gate to require that no kill switch (global or for this business) is active, so that a halted business cannot launch.
11. As a compliance owner, I want the readiness gate to require the lawful-basis / RoPA check to pass, so that no business processes personal data without a documented basis (ties launch to the Audit-4 control).
12. As a governance owner, I want a business that fails readiness to remain `draft` with its capital allocated but *locked*, so that committed capital is honestly on the books but unspendable until the business clears.
13. As a governance owner, I want a business's readiness re-checkable later, so that a business blocked by a transient condition (kill switch, incomplete RoPA) can be activated once it clears.
14. As a portfolio operator, I want each readiness failure to come with explicit reasons, so that I know exactly what to fix before a business can launch.
15. As a finance owner, I want to ask "can business B spend amount A?" and get a deterministic yes/no with a reason, so that spend decisions are governed and predictable.
16. As a finance owner, I want a spend refused when the business is not `active`, so that only launched businesses move money.
17. As a finance owner, I want a spend refused when the amount exceeds the business's remaining `<business_id>:cash`, so that a business cannot outspend its runway.
18. As a finance owner, I want a non-positive spend amount refused, so that malformed spends never pass the gate.
19. As a portfolio/executive consumer, I want a `BusinessActivated` event published when a business goes live, so that a portfolio layer can track the portfolio without reading the Factory's store.
20. As a portfolio operator, I want the set of businesses and their statuses to persist, so that which businesses exist and whether they are `active` survives restarts and can be queried.
21. As a developer, I want the Factory's decision logic (registry, readiness, can-spend) to be a pure module with injected inputs, so that it is fast and exhaustively testable without infrastructure.
22. As a developer, I want the persisted provisioning flow verified against real Postgres + the real ledger, so that capital allocation and activation are proven end-to-end.
23. As a developer, I want a one-command demo of provisioning and gating across more than one business, so that multi-tenancy is visibly working.
24. As a maintainer, I want the demo run as a CI gate, so that the Factory's guarantees are continuously verified.

## Implementation Decisions

- **New bounded context `ab_factory`**, split like `ab_ledger`: a pure **`core`** (no I/O) and a Postgres **`store`** (persistence + integrations). `Blueprint` stays in `ab_growth`; `ab_factory` depends on `ab_growth` (blueprint) and `ab_ledger` (capital).
- **Logical multi-tenancy.** A `business_id` scopes ledger accounts via the existing prefix convention: `<business_id>:cash` (the business's spendable balance) and the shared `portfolio:treasury`. No physical (schema/topic) isolation this slice.
- **Capital = double-entry ledger transaction.** Allocation books debit `<business_id>:cash` / credit `portfolio:treasury` through `ab_ledger.store.post`, preserving `trial_balance()==0`. `Blueprint.experiment_budget_minor` remains a per-experiment sub-cap enforced by the growth engine; the Factory's `capital_minor` is total runway and must be `≥` the experiment budget. `portfolio:treasury` is **unbounded** (goes negative = total capital deployed); a portfolio capital cap is out of scope.
- **Registry & lifecycle.** A persisted `businesses` record (`business_id` PK, `name`, `status`, `capital_minor`, `created_at`) with lifecycle `draft → active → sunset`. `provision()` sequence: reject if `capital_minor < experiment_budget_minor` (nothing written) → register `draft` → allocate capital → run readiness → `active` if ready else stays `draft` (capital locked).
- **Readiness gate = pure, injectable.** `readiness(business, *, cash_balance, kill_switch_clear, compliance_clear) -> Readiness(ready, reasons)` with three checks: capital funded (`cash_balance ≥ experiment_budget`), kill-switch clear, compliance clear. The `store`/service wires the real signals — `<business_id>:cash` from `ab_ledger`, `ab_killswitch` state, `ab_compliance.ropa.check()`.
- **Spend decision = pure.** `can_spend(business, amount_minor, *, cash_balance) -> (allowed, reason)`: allowed iff `status == active` and `0 < amount_minor ≤ cash_balance`. Not wired into `payments.transfer` this slice (that is the explicit next slice).
- **Event.** `BusinessActivated(business_id, name, capital_minor)` added to `ab_schemas` (internal classification), published by the `store` on activation (same pattern as `LedgerEntryPosted`).
- **Determinism boundary preserved.** All Factory logic is deterministic code; no model output touches capital, readiness, or spend.

## Testing Decisions

- **Good tests assert external behavior, not implementation** — the observable outcome of provisioning/readiness/can-spend, not private helpers.
- **Seam 1 (primary, pure `ab_factory.core`, infra-free):** underfunded provision rejected; a business reaches `active` iff all three readiness checks pass, else stays `draft` with reasons; re-checking readiness after a blocked condition clears activates it; `can_spend` allows on active+funds and denies on not-active / over-runway / non-positive. Prior art: `ab_ledger/tests/test_core.py`, `ab_ops/tests/test_reliability.py`, `ab_growth/tests`.
- **Seam 2 (integration, `ab_factory.store` vs Postgres):** after provisioning, the `businesses` row exists with the right status; `<business_id>:cash` equals the allocated capital and `trial_balance()==0`; an activated business publishes exactly one `BusinessActivated` on the bus. Prior art: `ab_ledger/tests/test_store.py`, `ab_gateway/tests/test_payments.py` (event-on-bus assertion), with a `conftest` truncating `businesses` + the ledger tables.
- **CI:** a `make factory` demo (infra-free, pure core across ≥2 businesses hitting active and blocked paths) runs as a pure gate alongside `make eval/ledger/compliance/failsim/growth`.

## Out of Scope

- **Half 2 — enforced spend:** wiring `can_spend` into `payments.transfer` (business-scoped payments, live readiness re-check at spend time). Explicit next slice.
- Portfolio capital cap (bounded/pre-funded treasury; reject over-allocation).
- Physical isolation (per-business schemas/topics/vector stores).
- Portfolio analytics / capital reallocation / living playbooks (a later portfolio context).
- Propagating `business_id` through the *existing* contexts' events/DB (decisions, audit) — this slice establishes the seam in the new context only.
- `sunset` mechanics beyond the state existing (capital reclamation flow).

## Further Notes

- **Issue tracker:** the configured tracker is GitHub Issues via `gh` (repo `oilyrags/autonomous-business-skeleton`); `gh` is not installed locally, so this PRD is drafted here and to be published (with `ready-for-agent`) once `gh` is available. Sliced issues are tracked locally under `.scratch/business-factory/` in the interim.
- **Autonomy:** provisioning and capital allocation are L2-ish governed actions (human-on-the-loop); the readiness gate is the launch blocker per architecture/16 standing rule ("no venture launches until audits 5/6/7 PASS for that surface").
