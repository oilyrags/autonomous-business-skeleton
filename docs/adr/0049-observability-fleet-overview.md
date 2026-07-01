---
status: accepted
---

# Observability: cost attribution + fleet overview + anomaly detection

Closes the P3 observability gap (cost attribution, anomaly detection, per-business + fleet overview)
as a deterministic query/rollup layer over the ledger — not a tracing vendor. PRD 0003; pure.

## Decisions

- **New `ab_obs` context**, pure, reading through a `LedgerView` port (`business_revenue` +
  `business_spend`, matched by `InMemoryLedger` and the Postgres store).
- **Cost attribution + health snapshot**: `snapshot(ledger, business_id, *, cogs, customers)`
  attributes revenue + llm/ad spend from the ledger and rolls it into unit economics
  (operating profit, LLM cost ratio, verdict).
- **Fleet overview**: `fleet_overview(ledger, configs)` snapshots every business; `fleet_totals`
  aggregates revenue/spend/profit and the unprofitable count — the whole portfolio at a glance.
- **Anomaly detection**: `detect_anomalies(snapshots, *, max_llm_cost_ratio_bps,
  operating_loss_floor_minor)` flags `LLM_COST_HIGH` (inference eating too much revenue) and
  `OPERATING_LOSS` (loss worse than the tolerated floor) — deterministic thresholds, no ML.

## Verified

3 pure tests (snapshot attributes ledger revenue/spend; fleet totals aggregate; anomalies flag the
LLM-hog + its loss while leaving the healthy business clean). `make obs` (in CI) prints the fleet
overview + anomalies. Full suite 215 passed, 36 skipped; ruff + mypy strict clean (99 files).

## Deferred

A real tracing backend (OTel/Phoenix) + dashboard UI on top of this layer; time-series/rate-of-change
anomalies (needs history); alert routing.
