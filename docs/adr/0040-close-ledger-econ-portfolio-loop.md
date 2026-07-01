---
status: accepted
---

# Close the ledger → econ → portfolio loop

The pieces existed but nothing joined them: the ledger knows per-business spend (ADR-0039), econ
turns spend + revenue into a profitability verdict (ADR-0034), and `allocate` already accepts an
injected `unprofitable_business_ids` set (ADR-0034 follow-up). This adds the one missing pure
connector + an end-to-end demonstration, so capital allocation runs on **real ledger money** rather
than a hand-picked set. The capstone of the portfolio/economics arc.

## Decisions

- **Pure connector `ab_econ.core.unprofitable_ids(economics) -> set[str]`** — the businesses whose
  verdict is UNPROFITABLE. Trivial but named and tested: the single definition of "who capital must
  not chase". `ab_portfolio` stays decoupled — it still just receives a set.
- **The loop is assembled by the caller**, dependency-directed and acyclic:
  `ledger.business_spend → UnitInputs(+injected revenue) → economics → unprofitable_ids →
  allocate(..., that_set)`. No context imports another it shouldn't.
- **Infra-free demo `make loop`** (in CI) over an in-memory ledger: two businesses that both *win*
  their experiments (score 4), but one bleeds money once its ledger LLM + ad spend is accounted for.
  The allocator funds the profitable winner and **holds** the money-loser — the guardrail firing on
  real spend, not a curated flag.

## Verified

- Pure: `unprofitable_ids` returns exactly the UNPROFITABLE ids (empty when all healthy). 2 tests.
- Capstone (pure, `InMemoryLedger`): seed two businesses' spend → derive economics with injected
  revenue → `unprofitable_ids` = the money-loser → `allocate` gives the profitable winner INVEST_MORE
  and holds the money-losing winner. 1 test. `make loop` prints the same story end to end.
- Full suite 171 passed, 36 skipped; ruff + mypy strict clean (81 files).

## Deferred

A revenue rail so revenue/cogs/customers are also sourced (removing the last injected input); a
service that runs this loop on a schedule and publishes `CapitalReallocationRecommended` for review.
