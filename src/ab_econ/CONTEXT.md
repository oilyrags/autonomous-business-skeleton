# Unit Economics

Turns a business's ledger spend + revenue into its economic health — CAC, margins, LTV, payback, P&L, and a profitability verdict that gates capital.

## Language

**Unit Economics**:
The per-business economic picture derived from inputs: operating profit, CAC, margins (bps), LTV, payback.
_Avoid_: metrics, KPIs (too broad)

**Contribution Margin**:
Revenue minus variable costs (cogs + LLM inference); acquisition spend is excluded (it drives payback).
_Avoid_: gross margin (gross margin also nets cogs but not the same line), profit

**Verdict**:
A business's profitability classification — PROFITABLE / BREAK_EVEN / UNPROFITABLE — the signal `ab_portfolio` consumes.
_Avoid_: status, health (informally)

**Payback Period**:
The number of periods of per-customer contribution needed to recover CAC; None when it never does.
_Avoid_: breakeven time, ROI period
