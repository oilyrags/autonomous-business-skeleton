---
status: accepted
---

# Portfolio capital-allocation engine

Planned with the spec-driven skills (grill → issue → tdd), acting on the recommendations' **P1
Multi-Business & Portfolio Management** (capital allocation, performance comparison, the portfolio
capital cap deferred from the Half-1 grill). A deterministic, recommend-only engine that recycles
capital from losing businesses into winners within a portfolio budget cap.

## Decisions (from the grilling session)

- **Performance signal:** `BusinessPerformance(business_id, capital_minor, scale/pivot/kill counts)`
  with `score = scale − kill` (net validated wins; pivots neutral) and `experiments = sum`
  (conclusiveness). Injected — the `ExperimentConcluded` bus rollup is a follow-up.
- **Four actions:** SUNSET (`score ≤ -2` and `experiments ≥ 3` — a *conclusive* loser),
  STARVE (`score < 0`, not conclusive — stop funding, on watch), INVEST_MORE (`score ≥ 2`), HOLD
  (everything else). Thresholds are named, env-overridable.
- **Recommend-only.** The engine returns `Recommendation`s and emits `CapitalReallocationRecommended`
  for human review; it performs **no ledger writes** — capital moves are human-in-the-loop
  (architecture/06, no L5 for money). Execution would flow through the already-governed money path.
- **Budget cap = the deferred bounded treasury.** `available = portfolio_budget − (Σcapital −
  Σsunset-reclaims)`; winners are funded greedily by score, each a fixed `reinvest_increment`, while
  capacity lasts; a winner that no longer fits is downgraded to HOLD ("budget exhausted"). Sunsets
  free capacity *first*, so recycling losers into winners is the core behaviour; the sum of deltas
  never pushes total deployed past the budget.
- **Pure core** (`ab_portfolio.core`) + `make portfolio` demo, mirroring `ab_growth` / `ab_ops` /
  `ab_factory.core`.

## Verified (TDD, one behaviour at a time)

- 6 pure tests: conclusive winner → INVEST_MORE; conclusive loser → SUNSET (`−capital`); marginal
  loser → STARVE and neutral → HOLD; a winner beyond the cap → HOLD (higher score funded first);
  sunset frees capacity to fund an otherwise-unfundable winner with net deployment within budget;
  recommendations become `CapitalReallocationRecommended` events. `make portfolio` shows all four
  actions + the cap downgrade (deployed 600k → 500k, within a 500k budget). lint + mypy strict clean.

## Deferred

The `ExperimentConcluded` bus rollup (subscribe + tally per business_id); executing an approved
reallocation through the Factory/ledger; cross-business "living playbook" pattern extraction.
