---
status: accepted
---

# Warehouse freshness SLA — trust the KPI, or know it is stale

A running semantic layer (ADR-0013) can silently fall behind the bus — a stalled
consumer or a failing dbt build leaves the served KPIs frozen while still returning
200s. A decision-intelligence context must be able to tell *how current* a metric is
before acting on it. This slice makes freshness a first-class, queryable property.

## Decisions

- **`ab_data.freshness`**: `read_freshness()` reads the observed state from silver —
  row count, newest `occurred_at` (business-event time), newest `ingested_at` (when the
  fabric last landed data). A **pure** `staleness(latest_ingested_at, now, sla_seconds)`
  turns that into an age + `within_sla` verdict — no clock in the query, so the trust
  decision is deterministic and unit-testable. SLA basis is *ingest* time (is the
  pipeline keeping up), configurable via `AB_FRESHNESS_SLA_SECONDS` (default 300s).
- **`GET /freshness`** on the data service returns rows, both timestamps, `age_seconds`,
  `within_sla`, `sla_seconds`. Never-ingested → `within_sla: false` (unknown = untrusted).
- **`/health` stays pure liveness.** Staleness is deliberately *not* folded into the
  container healthcheck: an idle-but-healthy service (no recent events) must not flap
  unhealthy and fail `make up --wait`. Readiness/staleness is a separate concern.
- **Freshness is not a quality check.** `quality.run_checks` stays clock-free
  (correctness/reconciliation); recency is operational signal exposed via the endpoint
  and the batch CLI (`make data` now prints row count + newest event).

## Store UTC, unambiguously

Fixed a latent ingest bug surfaced by freshness: binding a **tz-aware** datetime into a
DuckDB `TIMESTAMP` (no tz) column let DuckDB shift it to the *host's local time*, so a
13:00Z event round-tripped as 15:00 on a UTC+2 host. `ingest._utc_naive` now normalises
`occurred_at` + `ingested_at` to UTC wall-time before write, so the warehouse is UTC
regardless of host tz and `freshness` can safely read the naive columns back as UTC-aware.
(Earlier KPIs only counted rows, so the skew was invisible until now.)

## Verified

- Infra-free tests (`test_freshness.py`, +5, 14 data tests total): pure staleness for
  never-ingested / fresh / stale; `read_freshness` before build (0 rows, nulls) and after
  build (correct row count, newest `occurred_at` as UTC-aware, non-null ingest time).
- Live: rebuilt the data image; before events `/freshness` → `rows:0, within_sla:false`;
  after producing 3 real `AgentDecisionMade` → `rows:3`, UTC timestamps, `age ~4s`,
  `within_sla:true`. `data-verify.sh` asserts freshness within SLA right after ingest.

## Deferred

Freshness alerting / a `/ready` gate that fails when stale; per-metric freshness;
event-time (not just ingest-time) SLAs; wiring freshness into a decision-intelligence
consumer's trust check.
