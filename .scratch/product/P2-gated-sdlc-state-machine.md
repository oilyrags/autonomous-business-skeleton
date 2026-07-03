# P2 — Gated SDLC state machine + persistence

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
The deterministic gated pipeline a promoted initiative travels: **intake → spec → design → blueprint
→ scaffold → QA → launch**. A pure state-machine core advances an initiative one stage at a time;
each stage has a **deterministic gate** (charter conformance, tests-green, DPIA-trigger flag, budget
cap) and a failed gate **halts** the initiative (the instantiation-guide model). Persist via a
`product_initiatives` table + `ab_product/store.py` (mirrors `ab_growth/store.py`: `business_id`-
scoped, idempotent on `initiative_id`), and publish an event per stage transition. The human
launch/DPIA gates are represented as pending states here (their UI + approval land in P3).

## Acceptance criteria
- [ ] Pure stage/gate core: a conformant initiative advances through every stage; a failed gate
      halts it at that stage with a recorded reason (infra-free tests, independent expected values).
- [ ] `product_initiatives` table + store (`create`/`get`/`advance`/`list_by_business`), idempotent,
      `business_id`-scoped; a stage transition publishes its event.
- [ ] Launch + DPIA stages are surfaced as pending-human states (no auto-advance past them).
- [ ] Persist/transition happy path verified infra-gated (real Postgres); `ruff` + `mypy` + `pytest` green.

## Blocked by
- P1b (ProductInitiative + blueprint + scaffold).
