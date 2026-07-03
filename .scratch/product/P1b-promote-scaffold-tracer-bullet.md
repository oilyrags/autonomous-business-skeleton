# P1b — Governed promote → classify → blueprint → Scaffolder → conformance gate (tracer bullet)

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
The governed spine that turns a validated growth initiative into a charter-conformant scaffold.
A new governed gateway tool **`product.initiative.promote`** (tenant-bound via `authz`, OPA rule +
grant for `product.engineering_agent`, audited — the `growth.experiment.create` pattern) accepts a
**ProductInitiative** and: (1) `classify` deterministically decides **new business** (mint a
`business_id`) vs **extension** (attach to an existing one) with rationale — never an LLM decision;
(2) builds a **ProductBlueprint** (typed engineering spec; a stub spec provider stands in for the
LLM behind a `ProductModel` port); (3) runs the deterministic **Scaffolder** which, from the
`BusinessCharter` (P1a) + the blueprint, produces a **ScaffoldPlan** — a `business_id`-scoped
FastAPI + vendored-daisyUI product service themed by the charter, pre-wired to the governed loop
(a `StubScaffoldWriter` records the plan; a real writer emits to disk behind a port); (4) admits it
only if `charter_conformance` passes; (5) emits a `ProductScaffolded` event (AsyncAPI-documented).
Every business-rule refusal is an audited `ToolDenied`, never a 500.

## Acceptance criteria
- [ ] `ProductInitiative` + `ProductBlueprint` arg/spec models; `ProductScaffolded` event documented
      in the AsyncAPI spec (the contract test passes).
- [ ] `product.initiative.promote` registered in the tool `REGISTRY` (`write`, `sensitive`); OPA rule
      + `authz` grant present; unauthorized principal / cross-tenant / bad args → audited deny.
- [ ] `classify` returns NEW vs EXTENSION with rationale for representative initiatives (pure test).
- [ ] The Scaffolder produces a ScaffoldPlan whose service is `business_id`-scoped and themed by the
      charter; a non-conformant plan is rejected by the gate before any event/side effect.
- [ ] Infra-free tests for the pure paths + the deny paths; the persist/emit happy path may be
      infra-gated (mirror `test_growth_experiment.py`). `ruff` + `mypy --strict` + `pytest` green.

## Blocked by
- P1a (BusinessCharter + charter_conformance).
