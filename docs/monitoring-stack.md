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

## Deferred (M5)

The modern observability layer — Prometheus `/metrics` + OpenTelemetry instrumentation on the
services, Grafana dashboards, Alertmanager + SLO burn-rate routing — is planned on top of the same
checks (`.scratch/monitoring/M5-observability-stack.md`), so there is one definition per signal.
