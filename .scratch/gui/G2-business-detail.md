# G2 — Business Detail view (/business/<id>)

**Parent:** PRD 0006 / ADR-0056.

## What to build
A deep, organized per-business view. `viewmodels.business(business_id, ...)` (pure) assembles: unit
economics (profit, CAC, gross margin, LTV, payback from `ab_econ`), monitor checks for that business,
experiments summary, and compliance status — into a `BusinessView`. `GET /business/{id}` renders it;
unknown id → a calm 404 state. Reuses the G1 design system (sections via progressive disclosure).

## Acceptance criteria
- [ ] `business(...)` pure, returns economics + checks + experiments + compliance; unit-tested.
- [ ] `GET /business/{id}` 200 with the sections; unknown id → 404 state; tested via TestClient.
- [ ] business_id is a first-class route segment; per-business monitor checks tagged correctly.
- [ ] ruff + mypy strict clean; keyboard-navigable sections.

## Blocked by
- G1 (view-model + design system).
