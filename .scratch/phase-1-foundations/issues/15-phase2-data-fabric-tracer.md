# 15 — Phase 2 Core-data tracer: event → warehouse → gold → one canonical KPI

Status: done

## What to build

The trusted-data-fabric tracer: consume AgentDecisionMade → bronze (Parquet) → medallion
(dbt-duckdb) → gold → semantic layer with one canonical KPI, plus data-inventory
classification + a quality test. (Phase 2 / Data Platform context.)

## Acceptance criteria

- [x] Bronze ingestion from the event bus (`consume_to_bronze`) + `write_bronze` with
      `ingested_at` provenance; classification-at-ingestion (`ab_data.inventory`).
- [x] dbt-duckdb medallion: `silver_decisions` (typed, dedup by event_id) + `gold_decisions_by_agent`.
- [x] Metrics registry enforces exactly one canonical definition per KPI (register-twice raises);
      canonical KPI `decisions_recorded_total` queryable over the warehouse.
- [x] Data-quality checks (no null decision_id; gold reconciles to silver).
- [x] Verified infra-free (5 tests in the normal suite) + live (`make data`).

## Comments

**Done (2026-07-01).** ADR-0012. New `ab_data` package (Data Platform context): DuckDB +
Parquet lakehouse-lite, dbt-duckdb transforms, code-defined metrics registry (single-definition
invariant), inventory classification, quality checks, `consume_to_bronze` (Redpanda) + a
`make data` CLI. duckdb + dbt-duckdb added to the dev group (not in service images). Verified:
5 infra-free tests (metrics + full pipeline running real dbt) pass in the suite; `make data`
consumed 3 live events → KPIs `decisions_recorded_total=3`, `deciding_agents_total=2`, quality green.

**Deferred (ADR-0012):** Cube/MetricFlow, Iceberg+Trino+OpenMetadata, a containerized data
service, more KPIs + dbt tests + freshness SLAs.

## Blocked by

- Phase 1 (events emitted by the gateway)
