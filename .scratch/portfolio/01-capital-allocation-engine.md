# 01 — Portfolio capital-allocation engine

Status: todo
Triage: ready-for-agent  ·  Blocked by: none (uses ab_factory/ab_growth concepts)  ·  Recommendations P1

## What to build (pure core + demo, infra-free)

A deterministic, recommend-only engine that recycles capital from losing businesses into
winners, within a portfolio budget cap. Recommend-only: no ledger writes (capital moves are
human-in-the-loop per architecture/06).

- `BusinessPerformance(business_id, capital_minor, scale_count, pivot_count, kill_count)`
  with `score = scale − kill` and `experiments = scale + pivot + kill`.
- `Action`: SUNSET | STARVE | INVEST_MORE | HOLD. Thresholds (named, env-overridable):
  `SUNSET_FLOOR=-2`, `MIN_CONCLUSIVE=3`, `INVEST_THRESHOLD=2`, `REINVEST_INCREMENT_MINOR`.
- Classify: SUNSET if `score ≤ SUNSET_FLOOR and experiments ≥ MIN_CONCLUSIVE`; else INVEST_MORE
  if `score ≥ INVEST_THRESHOLD` (subject to budget); else STARVE if `score < 0`; else HOLD.
- Budget cap: `available = portfolio_budget − (Σcapital − Σsunset-reclaimed)`; fund INVEST_MORE
  winners greedily by score desc, each `reinvest_increment`, while capacity remains; a winner that
  no longer fits → HOLD ("winner, but portfolio budget exhausted").
- `Recommendation(business_id, action, capital_delta, reason)` — `+increment` invest, `−capital`
  sunset, `0` else. Output preserves input order (deterministic).
- `CapitalReallocationRecommended(business_id, action, capital_delta, reason)` event in ab_schemas;
  `to_events()` helper.
- `make portfolio` (in CI): infra-free demo over a small portfolio hitting all four actions +
  the budget-cap downgrade.

## Acceptance criteria

- [ ] A conclusive loser (score ≤ -2, experiments ≥ 3) → SUNSET with `capital_delta = −capital`.
- [ ] A conclusive winner (score ≥ 2) with capacity → INVEST_MORE with `+increment`.
- [ ] A net-negative but inconclusive business → STARVE (delta 0); neutral → HOLD (delta 0).
- [ ] Total recommended new deployment never exceeds `portfolio_budget` (sunsets free capacity first).
- [ ] A winner that doesn't fit the remaining budget → HOLD ("budget exhausted"), delta 0.
- [ ] `CapitalReallocationRecommended` carries business_id/action/capital_delta.
- [ ] `make portfolio` infra-free, all four actions shown; green in CI. ruff + mypy clean.

## Blocked by
None.
