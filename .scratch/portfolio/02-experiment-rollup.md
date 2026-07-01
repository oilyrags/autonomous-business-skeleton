# Slice 41 — Portfolio rollup: ExperimentConcluded → BusinessPerformance

**Why.** The `allocate` engine (slice 40) takes injected `BusinessPerformance`. This slice
builds the injection: fold the growth context's published `ExperimentConcluded` events into
per-business performance tallies, so the portfolio decides on *real* outcomes. Closes the
"bus rollup deferred" note in ADR-0033.

**Shape (pure, no I/O — matches ab_growth / ab_portfolio.core style).**
`ab_portfolio.rollup.rollup(events, *, capital_by_business) -> list[BusinessPerformance]`

- Tally per `business_id`: `scale` → scale_count, `pivot` → pivot_count, `kill` → kill_count.
- `continue` is **not a conclusion** — it does not count toward any tally (inconclusive, still
  running). It must not create a business with all-zero counts either.
- `capital_minor` comes from the injected `capital_by_business` mapping (the ledger balance —
  the portfolio does not re-derive money from events); missing → 0.
- Output preserves first-seen `business_id` order; one `BusinessPerformance` per business that
  has at least one *concluded* (scale/pivot/kill) outcome.

**Behaviors to test (one at a time).**
1. One `scale` event → one BusinessPerformance, scale_count=1, capital from the map.
2. Mixed scale/pivot/kill for one business → counts tallied; score/experiments derive correctly.
3. Two businesses → two performances, first-seen order, tallies isolated per business_id.
4. `continue` events are ignored — a business with only `continue` produces no performance.
5. Missing capital in the map → capital_minor=0 (safe default).

Recommend-only downstream unchanged; no ledger writes. ruff + mypy-strict clean; unique test
basename `test_portfolio_rollup.py`.
