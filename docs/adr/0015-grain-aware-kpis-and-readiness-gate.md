---
status: accepted
---

# Grain-aware KPIs + a readiness gate

Builds on the freshness work (ADR-0014). Two increments toward a semantic layer a
decision-intelligence context can actually depend on: a **time-grained** data product
(not just all-time totals), and a **readiness gate** that gives a single yes/no on
whether the served data is trustworthy right now.

## Decisions

- **Daily grain, end-to-end.** New dbt model `gold_decisions_by_day` (UTC day →
  `decision_count`), a new quality check `gold_by_day_reconciles_to_silver`, and a new
  canonical KPI `active_decision_days_total` (grain `daily`) — distinct UTC days with a
  decision. The metrics registry contract stays **scalar-per-KPI**; the day rollup is
  served as a *series* rather than shoehorned into a scalar metric.
- **`GET /series/decisions_by_day`** serves the grain-aware breakdown (oldest first,
  `{day, decision_count}`); empty list before the warehouse is built.
- **`GET /ready`** — readiness, distinct from `/health` (liveness). 200 only if the
  warehouse is built AND within the freshness SLA; else **503** with a reason. Backed by
  a pure `freshness.readiness(Freshness, now, sla)` helper so the verdict is
  deterministic and unit-testable. Consumers gate on `/ready`; orchestration keeps using
  `/health` so an idle-but-live service never flaps.
- **No wall-clock windows in the registry.** Deliberately avoided "last 7 days"-style
  metrics for now: they depend on `now()` inside the query and would make KPIs
  non-deterministic to test. Grain-awareness here = an explicit day dimension, not a
  moving window. (Moving-window metrics are deferred until we thread a reference clock.)

## Verified

- Infra-free tests (+6, 20 data tests total): readiness pure helper (not-built / stale /
  ready); `active_decision_days_total` = 2 over a two-day fixture; `/series/decisions_by_day`
  exact rows + ordering; empty series before build; `/ready` 503-before / 200-after.
- Live: produced 3 real decisions across two UTC days → `/ready` 503→200,
  `active_decision_days_total` = 2, `/series/decisions_by_day` = `[{06-29: 2}, {06-30: 1}]`,
  registry now lists 3 canonical KPIs. `data-verify.sh` asserts `/ready` 200 + a
  reconciling non-empty series.

## Deferred

Moving-window / event-time KPIs (need an injected reference clock); per-metric grains
beyond daily; freshness alerting; wiring `/ready` into a real consumer's trust check;
Cube / dbt-MetricFlow.
