# Monitoring stack (Nagios/Icinga2 integration)

`ab_monitor` turns the skeleton's deterministic signals into **Nagios plugin check results**
(status + output + perfdata) — consumed unchanged by Nagios Core, Icinga2, or Naemon. See ADR-0055 /
PRD 0005 for the design and the full plan.

## Try it (no infra)

```
make monitor        # evaluate the check suite, print Nagios plugin lines
```

The pure checks and the Icinga2 payload builder are covered in CI (`make test`).

## Submit to a live Icinga2 (M4 — deferred infra)

Bring up the monitoring profile (secrets come from the environment, never committed):

```
ICINGA2_API_PASSWORD=changeme ICINGAWEB2_ADMIN_PASSWORD=changeme \
  docker compose -f docker-compose.monitoring.yml up -d
```

- **Icinga2 REST API** — `https://localhost:5665` (target of `process-check-result` submissions)
- **Icinga Web 2** — `http://localhost:8080` (operator UI)

Submit the check suite through the `Icinga2RestExporter` (the real adapter behind the
`NagiosExporter` port):

```
ICINGA2_API_PASSWORD=changeme ICINGA2_VERIFY=false make monitor-submit
```

The integration test (`test_monitor_submit_integration.py`) exercises this path and **skips fast**
when the profile isn't reachable, so CI stays green without infra.

## Swapping the target

Because the port emits the vendor-neutral Nagios plugin protocol, the classic-Nagios alternative
submits the same `CheckResult`s via **NSCA** behind the same `NagiosExporter` port — implement an
`NscaExporter` and pass it wherever `Icinga2RestExporter` is used; nothing else changes.

## M5 — metrics, dashboards, alert routing

The same deterministic checks and business reads feed Prometheus (one definition per signal, two
consumers):

- **`/metrics` on the console** (`http://localhost:8600/metrics`) — a pure, hand-rolled Prometheus
  text exposition (`ab_monitor/prometheus.py`; no `prometheus-client` dependency): every check as
  `ab_check_status` (+ perfdata and warn/crit thresholds as series) and per-business economics
  (`ab_business_*`, `ab_fleet_*`), all tagged `business_id`.
- **Version-controlled config** under `monitoring/`: Prometheus scrape + **SLO burn-rate rules**
  (`ab:error_budget_burn:ratio` from the `ab_ops` error-budget perfdata; `ErrorBudgetBurnHigh`,
  `CheckCritical`, `BusinessUnprofitable` alerts with runbook links), Alertmanager routing (grouped
  by `alertname` + `business_id`; wire your pager in `alertmanager.yml`), and a provisioned Grafana
  **Fleet Overview** dashboard (`monitoring/grafana/dashboards/fleet-overview.json`).
- **Bring it up** (with the Icinga2 profile or standalone):

```
GRAFANA_ADMIN_PASSWORD=changeme ICINGA2_API_PASSWORD=changeme ICINGAWEB2_ADMIN_PASSWORD=changeme \
  docker compose -f docker-compose.monitoring.yml up -d
make console-serve   # the scrape target
```

Prometheus: `http://localhost:9090` · Grafana: `http://localhost:3000` · Alertmanager: `http://localhost:9093`.

**OpenTelemetry SDK instrumentation is deliberately deferred**: it would add several
`opentelemetry-*` dependencies to every service for tracing we don't yet consume; the event
envelope already carries `trace_id` for correlation. Revisit when a tracing backend is actually
operated.
