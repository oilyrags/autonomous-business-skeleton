---
status: accepted
---

# Phase 2 data platform: DuckDB + Parquet + dbt, code-defined semantic layer

The first Core-data slice is a **data-fabric tracer**: `AgentDecisionMade` events →
bronze (Parquet) → medallion (dbt-duckdb) → gold → semantic layer with **one canonical
definition per KPI**. Deliberately lakehouse-lite instead of the full stack-doc target
(Iceberg + Trino + Cube + OpenMetadata).

## Decisions

- **Warehouse:** DuckDB (embedded, no server) with Parquet medallion storage. `ab_data`.
- **Transforms:** dbt-duckdb — `silver_decisions` (typed, de-duplicated by event_id) and
  `gold_decisions_by_agent`. Run via `dbt build` in the pipeline.
- **Semantic layer:** a **code-defined metrics registry** (`ab_data.metrics.REGISTRY`) that
  enforces the invariant *exactly one canonical definition per KPI* — registering a name
  twice raises. This is the Phase-2 success metric and a `16` data-audit criterion, proven
  by a unit test, rather than standing up a Cube server for the tracer.
- **Ingestion:** event-driven — `consume_to_bronze` reads `AgentDecisionMade` off Redpanda;
  `write_bronze` lands typed rows + `ingested_at` provenance. Classification-at-ingestion via
  `ab_data.inventory` (architecture/08 schema).
- **Quality:** `no_null_decision_id` + `gold_reconciles_to_silver` run after the build.
- **Packaging:** `duckdb` + `dbt-duckdb` live in the `dev` dependency group (pipeline + tests
  run via `uv run`/CI, not in the service images). The pipeline is a batch job/CLI
  (`make data`), not yet a running service.

## Verified

- Infra-free tests (run in the normal suite): metrics single-definition enforcement; and the
  full pipeline from synthetic events → dbt → canonical KPI + quality (5 tests).
- Live: `make data` consumed real events off Redpanda and printed
  `decisions_recorded_total` / `deciding_agents_total` with quality green.

## Deferred

Cube / dbt-MetricFlow semantic-layer server; Iceberg + Trino + OpenMetadata; a long-running
data service (containerized consumer); more KPIs, dbt tests, and freshness SLAs.
