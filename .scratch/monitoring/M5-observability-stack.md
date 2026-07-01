# M5 — Observability stack: Prometheus + OTel + Grafana + Alertmanager (deferred infra)

**Parent:** PRD 0005 / ADR-0055. **Triage:** ready-for-agent. **Deferred infra** — the modern
metrics/traces/dashboards layer on top of the same checks; needs the running mesh.

## What to build

The monitoring.md observability stack, layered on the deterministic checks rather than replacing
them. In rough order:
1. **Metrics**: a Prometheus `/metrics` endpoint on the FastAPI services (gateway/agent/data/…),
   plus the `ab_monitor` perfdata exposed as Prometheus series (business metrics tagged
   `business_id`: revenue, experiment outcomes, cost vs revenue, agent-decision success).
2. **OpenTelemetry** instrumentation of the services (traces + metrics via OTLP → an OTel collector),
   correlated by `trace_id` (the envelope already carries one).
3. **Grafana** dashboards provisioned from JSON (Fleet Overview, Service Health / golden signals,
   Business Health per `business_id`, Infra & Security), + Prometheus + a `docker-compose` addition.
4. **Alerting**: SLO **burn-rate** alert rules (reusing the `ab_ops` error-budget definition) +
   Alertmanager routing (grouping, dedup, escalation) with rich context (business_id, runbook link).

Each sub-step is its own PR-sized issue when this phase starts; keep the checks (M1–M3) as the source
of truth and derive metrics/alerts from them so there is one definition per signal.

## Acceptance criteria (phase-level)

- [ ] Services expose Prometheus `/metrics`; key business + SLO series are scrape-able, `business_id`-
      tagged.
- [ ] OTel traces flow to a collector and correlate with logs by `trace_id`.
- [ ] Grafana dashboards provisioned as version-controlled JSON; Prometheus + Grafana in a compose
      profile.
- [ ] SLO burn-rate alerts + Alertmanager routing with runbook/dashboard links; no raw-threshold
      CPU alerts.
- [ ] No secrets committed; docs for bringing the stack up.

## Blocked by

- M1 (the checks are the source of truth); independent of M4 (Nagios) — can run in parallel.
