---
status: accepted
---

# Per-business unit economics + LLM cost-budget guard

Acting on the recommendations' **P3 Economics / Cost Control** (per-business LLM cost budgets +
unit-economics KPIs). The portfolio engine (ADR-0033) scores businesses on scale/kill *counts* — it
cannot yet see whether a business actually *makes money*. This adds the deterministic economic
signal. Spec-driven (issue → tdd); pure, infra-free.

## Decisions

- **New thin context `ab_econ.core`** — not `ab_data` (warehouse/metrics infra) and not `ab_growth`
  (experiment stats). Unit economics is a decoupled, pure, injectable concern.
- **Ledger-shaped injected inputs:** `UnitInputs(business_id, revenue_minor, cogs_minor,
  ad_spend_minor, llm_spend_minor, customers)`, all `ge=0`. LLM inference cost is **first-class**
  (separate from cogs) because per-business LLM budgets are the explicit ask.
- **Money stays integer minor units** (like the ledger); ratios are **integer basis points**
  (bps, /10000), floor division — consistent with `ab_growth`'s `cac_minor = spend // conversions`.
- **KPIs** (`economics(inputs) -> UnitEconomics`):
  - `operating_profit_minor = revenue − cogs − ad − llm` (all-in).
  - `cac_minor = ad_spend // customers` (None if no customers).
  - `gross_margin_bps = ((revenue − cogs − llm) * 10000) // revenue` (None if revenue 0).
  - `llm_cost_ratio_bps = (llm * 10000) // revenue` (None if revenue 0) — the LLM-budget lens.
  - `verdict`: PROFITABLE / BREAK_EVEN / UNPROFITABLE by operating-profit sign.
- **Cost-budget guard:** `within_llm_budget(inputs, *, llm_budget_minor) -> bool` — a thin
  deterministic decision mirroring `ab_factory.can_spend`; the seam a gateway or the portfolio can
  call before authorising further model spend for a business.
- **Report-only** — no ledger writes, no events this slice.

## Verified (TDD, one behaviour at a time)

6 pure tests: profitable verdict + operating profit; CAC (and None without customers); gross
margin bps (and None at zero revenue); LLM cost ratio bps; loss-making → UNPROFITABLE; the budget
guard at/under/over. `make econ` (in CI) contrasts a healthy business (profit +650k, LLM 5% of
revenue, within budget) with an LLM-hog (loss −150k, LLM 83% of revenue, over budget). ruff +
mypy strict clean.

## Follow-up shipped — profit gates allocation (slice 43)

`allocate` now takes an optional injected `unprofitable_business_ids: Container[str]` (default
empty — backward compatible). A **winner that is unprofitable is not funded**: it is downgraded to
HOLD ("winner but unprofitable — fix economics before funding") and does **not** consume budget, so
its headroom stays available for a profitable lower-score winner. `ab_portfolio` stays decoupled
(no `ab_econ` import — the caller passes the set); economics gates INVEST_MORE only. This ties the
pipeline together: **growth → rollup → econ → portfolio**. 2 new pure tests (unprofitable winner
held; its budget freed for a profitable one).

## Deferred

Enforcing `within_llm_budget` at the Portkey gateway before a model call; sourcing the economics
inputs from the ledger + a real ad/revenue rail; a live consumer that maintains the unprofitable
set from `ExperimentConcluded` + ledger balances.
