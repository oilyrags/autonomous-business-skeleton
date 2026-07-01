---
status: accepted
---

# Data service: the semantic layer as a long-running, queryable component

ADR-0012 shipped the Core-data pipeline as a batch job/CLI (`make data`) and deferred a
long-running data service. This slice promotes it to a **containerized service** that
continuously consumes `AgentDecisionMade` off the bus, rebuilds the medallion, and serves
the **canonical KPIs over HTTP** — so other contexts (e.g. Executive / decision
intelligence) can query trusted metrics instead of re-deriving them.

## Decisions

- **Service, not batch:** `ab_data.app` (FastAPI) runs a background thread that loops
  `consume_to_bronze` → (if new events) `pipeline.build`. The batch CLI (`make data`) is
  kept for one-shot runs; both share the same ingest/build code.
- **HTTP semantic layer:** `GET /metrics` lists the canonical registry (name, description,
  grain); `GET /metrics/{name}` returns the single scalar value; unknown metric → **404**
  (never a fabricated number); warehouse-not-yet-built → `value: null` + a note.
- **Append-only bronze:** `write_bronze` now writes a new Parquet *part* per batch
  (`bronze/agent_decisions/part-*.parquet`) instead of overwriting one file, so a
  long-running service accumulates events over time. `silver_decisions` reads a glob and
  still de-duplicates by `event_id` (idempotent re-consumption is safe).
- **Own lean image:** `Dockerfile.data` installs main deps + the new `data` dependency
  group (`duckdb` + `dbt-duckdb`) only — the 5 app-service images stay lean (they build
  with `--no-dev` and no `data` group). `dev` includes the `data` group so tests/CI keep it.
- **Its own warehouse volume:** the service owns a `data-warehouse` Docker volume mounted at
  `/warehouse` (`AB_WAREHOUSE_DIR`). It consumes Redpanda in plaintext on the internal
  network (bus mTLS is still deferred — see PROJECT §4).
- **Single-writer discipline:** a process lock serialises warehouse access (DuckDB is
  single-writer); the read endpoints open read-only connections under the same lock.

## Verified

- Infra-free tests (in the normal suite, `test_app.py`, +4): registry listing; unknown
  metric → 404; warehouse-not-built → `null` + note; and served value after a real build.
- Live (`make up` runs the service; `make data-verify` / `scripts/data-verify.sh`): drove
  real decisions through the mTLS'd agent→gateway path, then the data service consumed them
  off the bus, rebuilt the warehouse, and served `decisions_recorded_total` /
  `deciding_agents_total`. Manually reproduced end-to-end against Redpanda: producing 3 then
  2 more `AgentDecisionMade` moved `decisions_recorded_total` 3 → 5 and
  `deciding_agents_total` 2 → 3 (append-only accumulation), unknown metric → 404.

## Deferred

Bus consumption over mTLS (gateway→Redpanda and service→Redpanda); time-windowed / grain-aware
KPIs; freshness SLAs and a `/health` that reflects warehouse staleness; Cube / dbt-MetricFlow
server; Iceberg + Trino + OpenMetadata.
