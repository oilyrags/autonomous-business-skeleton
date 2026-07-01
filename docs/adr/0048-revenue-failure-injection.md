---
status: accepted
---

# Revenue & multi-business failure-injection scenarios

Closes the P4 "expand failure-injection to cover revenue experiment scenarios and multi-business
interactions" gap. Four new scenarios drive the real revenue/portfolio/econ/gateway controls with
injected faults and assert containment. PRD 0003; extends the Audit-12 suite (ADR-0012 family).

## Scenarios added (all CONTAINED, deterministic, no infra)

- **losing_business_sunset** — a business with conclusive experiment losses is SUNSET by the
  allocator and its capital reclaimed (a runaway loser can't keep consuming capital).
- **over_budget_llm_call** — a model call that would breach the per-business LLM budget is refused
  by the gateway gate before any inference.
- **cross_business_isolation** — business A's LLM spend and business B's revenue stay attributed to
  their own `business_id`; neither leaks into the other (multi-tenancy holds under mixed activity).
- **unprofitable_winner_held** — a business that wins its experiments but loses money is held by the
  econ→portfolio loop (capital never chases a money-loser, even a high-scoring one).

## Verified

`make failsim` (in CI): **11 contained, 0 breach, 0 deferred** (7 original + 4 new). The count test
updated to 11. Full suite 212 passed, 36 skipped; ruff + mypy strict clean (96 files).

## Deferred

Fault injection against the live gateway/ledger integration path (needs infra); chaos over the bus.
