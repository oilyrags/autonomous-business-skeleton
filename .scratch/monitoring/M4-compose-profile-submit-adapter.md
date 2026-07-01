# M4 — Monitoring compose profile + real submit adapter (deferred infra)

**Parent:** PRD 0005 / ADR-0055. **Triage:** ready-for-agent. **Deferred infra** — needs the running
stack; the integration test skips fast without infra.

## What to build

Make the checks land in a real monitoring system. A `docker-compose.monitoring.yml` profile bringing
up Nagios (or Icinga2 + Icinga Web) reachable from the mesh, and a **real submit adapter behind the
`NagiosExporter` port**:
- `NscaExporter` — submit passive check results via NSCA / `check_mrpe` (classic Nagios), OR
- `Icinga2RestExporter` — submit via the Icinga2 `process-check-result` REST API.

The same `CheckResult`s from M1–M3 flow through the chosen adapter unchanged (that's the point of the
vendor-neutral contract). A `make monitor-submit` (or a scheduled submitter) pushes the suite on a
cadence. An integration test asserts a result reaches the monitoring system; it **skips fast when the
monitoring container isn't reachable** (socket check first, like `test_business_spend_store.py`).

## Acceptance criteria

- [ ] `docker-compose.monitoring.yml` profile: Nagios/Icinga2 (+ web UI) on the monitoring network,
      with credentials via env, not committed.
- [ ] A real submit adapter implements `NagiosExporter` (NSCA or Icinga2 REST); callers unchanged.
- [ ] Integration test: a `CheckResult` submitted through the adapter appears in the monitoring
      system; skips fast without the container. Secrets never committed.
- [ ] Docs: how to bring up the profile and point it at the exporter.

## Blocked by

- M1 (the exporter port); benefits from M2 + M3 (more checks to submit).
