---
status: accepted
---

# ab_monitor — Nagios monitoring integration

Plans the monitoring/observability capability from `monitoring.md` (Nagios/Icinga2 + the modern
observability stack) as a **skeleton-native bounded context**, not the standalone external stack.
Designed via `/grill-with-docs`; two decisions were put to the owner, the rest follow the repo's
rules (determinism boundary; reuse of `ab_ops`/`ab_obs`; `business_id` multi-tenancy).

## Decisions (grilled)

1. **Skeleton-native `ab_monitor`, ports + stubs.** A new `src/ab_monitor/` context: deterministic
   health/SLO/business-health aggregation that **reuses existing signals** — `ab_ops` (error budget,
   severity), `ab_obs` (fleet overview, anomalies), the services' `/health` endpoints, and the
   money/identity invariants — turned into check results. A `NagiosExporter` **port** (stub by
   default) with real submit adapters behind it. Runs end-to-end in CI on stubs. *Not* the standalone
   Icinga2/Prometheus/Grafana deployment (that's a deferred infra phase).
2. **Vendor-neutral Nagios plugin protocol as the port contract.** A `CheckResult` is the classic
   plugin result: **status** (OK=0 / WARNING=1 / CRITICAL=2 / UNKNOWN=3), a plugin-output line, and
   **perfdata** (`label=value;warn;crit`). Consumed unchanged by **Nagios Core, Icinga2, and Naemon**
   — the widest, most durable contract. Real adapters submit via NSCA / `check_mrpe` (Nagios) or the
   Icinga2 `process-check-result` REST API; the stub just formats.

## Determinism split & reuse (not grilled)

- **Deterministic** (pure cores): a `Check` evaluates a signal against thresholds → a `CheckResult`.
  SLO **burn rate** reuses `ab_ops.ErrorBudget`; **per-business health** reuses `ab_obs`
  (`detect_anomalies`, `fleet_overview` → WARNING/CRITICAL); **invariants** (ledger `trial_balance()
  == 0`, audit hash-chain integrity, kill-switch status) are CRITICAL checks. No signal is reinvented.
- **Behind a port / deferred infra**: submitting results to a live Nagios/Icinga2; the
  docker-compose monitoring profile; Prometheus `/metrics` + OpenTelemetry instrumentation of the
  FastAPI services; Grafana dashboards; Alertmanager routing. These need the running mesh + infra.
- **Multi-tenancy**: every check carries an optional `business_id`; per-business checks are generated
  from the active businesses (dynamic service definitions).

## Glossary (to land in `src/ab_monitor/CONTEXT.md` at build time)

- **Check** — a named evaluation of one signal against thresholds, producing a `CheckResult`.
- **Check Result** — status (OK/WARNING/CRITICAL/UNKNOWN) + plugin output + perfdata; the Nagios
  plugin contract. _Avoid_: alert, health status (informally).
- **Perfdata** — machine-readable `label=value;warn;crit` metrics on a check, for graphing.
- **SLO Burn Rate** — how fast an error budget (`ab_ops`) is consumed; the basis for alerting over
  raw thresholds.
- **Nagios Exporter (port)** — the seam that renders/submits check results in the plugin protocol;
  stub by default, NSCA/Icinga2-REST adapters behind it.

## Plan shape (near-term buildable vs deferred)

Buildable now (CI-runnable, ports+stubs): the check model + registry + core service/infra/invariant
checks + per-business checks (reusing ab_obs) + the `NagiosExporter` port + stub + a `make monitor`
demo. Deferred infra phases (need the mesh): the compose monitoring profile + a real submit adapter;
then Prometheus/OTel instrumentation + Grafana dashboards + Alertmanager/SLO burn-rate alerting.

Full detail: PRD 0005; issues in `.scratch/monitoring/`.
