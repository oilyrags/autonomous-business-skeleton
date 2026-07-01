---
status: accepted
---

# Unit economics: contribution margin, LTV, payback, P&L

Closes the P3 "unit economics (CAC, LTV, contribution margin, payback period) underdeveloped" gap.
Extends `ab_econ` with the full KPI set + a per-business P&L. PRD 0003; spec-driven; pure, integer
minor units.

## Decisions

- **Contribution margin** = revenue − variable costs (cogs + llm inference); acquisition (ad) spend
  is excluded — it's a customer-acquisition cost accounted for separately in payback.
- **LTV** = per-customer contribution × `expected_lifetime_periods` (new optional arg to
  `economics`, default 1); None without customers.
- **Payback periods** = ceil(CAC / per-customer contribution) via integer ceil-division; None when
  per-customer contribution is ≤ 0 (never pays back).
- **`profit_and_loss(inputs) -> ProfitAndLoss`** rolls the lines up: revenue, cogs, llm, ad,
  gross_profit (revenue−cogs), contribution_margin (−llm), operating_profit (−ad).
- All money integer minor units; division floors (LTV/payback), consistent with the rest of `ab_econ`.

## Verified

6 pure tests (contribution excludes acquisition; LTV = per-customer × lifetime; LTV None without
customers; payback recovers CAC; payback None when contribution ≤ 0; P&L roll-up). `make econ` now
prints contribution/LTV/payback. Full suite 207 passed, 36 skipped; ruff + mypy strict clean.

## Deferred

Retention/churn-driven LTV (needs cohort data); discounting; multi-period P&L history.
