# G4 — Experiments view

**Parent:** PRD 0006 / ADR-0056.

## What to build
List + result view for experiments with statistical context. `viewmodels.experiments(...)` (pure)
summarizes `ab_growth` outcomes (action scale/pivot/kill/continue, p-value, lift, conversion rates)
per business into an `ExperimentsView`. `GET /experiments` (and a per-business filter) renders it,
making the evidence legible (significance, KPI vs target) without hiding the numbers.

## Acceptance criteria
- [ ] `experiments(...)` pure, returns per-experiment summaries with action + stats; unit-tested.
- [ ] `GET /experiments` 200, `?business_id=` filter works; tested via TestClient.
- [ ] Result view shows p-value/lift/decision clearly (deference to the data). ruff + mypy clean.

## Blocked by
- G1.
