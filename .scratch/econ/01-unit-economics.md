# Slice 42 — ab_econ: per-business unit economics + LLM cost-budget guard (P3)

**Why.** The portfolio scores businesses on scale/kill *counts* — it cannot yet see whether a
business actually *makes money*. The recommendations' P3 asks for per-business LLM cost budgets +
unit-economics KPIs (CAC / margin / burn). This is the deterministic economic signal that later
feeds the portfolio's capital decision. Pure, infra-free, integer minor units (no floats for money,
like the ledger) — ratios expressed in integer basis points.

**Self-grilled decisions (recommendations noted).**
1. **Home:** a new thin context `ab_econ.core` (not ab_data — that's warehouse/metrics infra; not
   ab_growth — that's experiment stats). Keeps unit economics a decoupled, pure, injectable concern.
2. **Inputs — injected, ledger-shaped:** `UnitInputs(business_id, revenue_minor, cogs_minor,
   ad_spend_minor, llm_spend_minor, customers)`, all `ge=0`. LLM inference cost is first-class
   (separate from cogs) because per-business LLM budgets are the explicit ask.
3. **Money stays integer; ratios are integer basis points** (bps, /10000). Floor division, matching
   `ab_growth`'s `cac_minor = spend // conversions`.
4. **Derived KPIs:**
   - `operating_profit_minor = revenue − cogs − ad − llm` (all-in).
   - `cac_minor = ad_spend // customers` (None if no customers) — acquisition cost per customer.
   - `gross_margin_bps = ((revenue − cogs − llm) * 10000) // revenue` (None if revenue 0).
   - `llm_cost_ratio_bps = (llm * 10000) // revenue` (None if revenue 0) — the LLM-budget lens:
     how much of revenue the model eats.
   - `verdict`: PROFITABLE (operating_profit > 0) / BREAK_EVEN (== 0) / UNPROFITABLE (< 0).
5. **Cost-budget guard (thin decision, mirrors ab_factory.can_spend):**
   `within_llm_budget(inputs, *, llm_budget_minor) -> bool` = `llm_spend_minor <= llm_budget_minor`.
6. **Recommend/report-only** — no ledger writes, no events this slice (feeding the portfolio score
   is an explicit follow-up).

**Behaviors to test (one at a time).**
1. Profitable business → operating_profit positive, verdict PROFITABLE.
2. `cac_minor` = ad_spend // customers; None when customers == 0.
3. `gross_margin_bps` from revenue/cogs/llm; None when revenue == 0.
4. `llm_cost_ratio_bps` reflects the LLM share of revenue; None when revenue == 0.
5. Loss-making inputs → operating_profit negative, verdict UNPROFITABLE.
6. `within_llm_budget` — True at/under budget, False over.

**Wiring.** `make econ` demo (in CI) across two businesses (one healthy, one bleeding on LLM cost).
ruff + mypy-strict clean; unique test basename `test_econ_core.py`.
