# Slice 43 — Profit gates the portfolio's INVEST_MORE

**Why.** `allocate` (slice 40) funds any business whose `score = scale − kill` clears the invest
threshold — it will pour capital into a business that wins experiments while *losing money*. The
`ab_econ` verdict (slice 42) is exactly the missing guardrail. This ties the pipeline together:
growth → rollup → **econ** → portfolio.

**Decision (keep ab_portfolio decoupled).** Don't import `ab_econ` into `ab_portfolio`. Add an
optional injected set of loss-makers:
`allocate(..., unprofitable_business_ids: Container[str] = frozenset())`.
The caller (who has the economics) passes the set. A **winner that is unprofitable is not funded** —
it is downgraded to HOLD ("winner but unprofitable — fix economics before funding") and, crucially,
**does not consume budget**, so a profitable lower-score winner can be funded from that headroom.

Scope stays minimal: economics gates **INVEST_MORE only**. SUNSET/STARVE/HOLD classification is
unchanged (an unprofitable loser is already handled by score). Backward compatible — default empty
set reproduces slice-40 behaviour exactly.

**Behaviors to test.**
1. Default (no set) → unchanged: a winner still gets INVEST_MORE.
2. A winner in the unprofitable set → HOLD, reason mentions economics, `capital_delta == 0`.
3. An unprofitable winner frees its budget for a profitable lower-score winner (the profitable one
   is funded even though it sorts second by score).

**Wiring.** `make portfolio` unchanged (no loss-makers in the demo set). ruff + mypy-strict clean.
