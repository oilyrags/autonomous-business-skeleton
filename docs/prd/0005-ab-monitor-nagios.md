# PRD 0005 — ab_monitor: Nagios monitoring integration

> Triage: `ready-for-agent`. Source: `monitoring.md`. Design: ADR-0055 (grilled). Tracker: no `gh`
> → issues under `.scratch/monitoring/`. Builds on `ab_ops`, `ab_obs`, the `/health` endpoints, the
> ledger/audit/killswitch invariants, and the docker-compose stack.

## Problem Statement

The skeleton has strong *raw* signals — `/health` endpoints, `ab_ops` error budgets, `ab_obs`
fleet/anomaly health, the audit hash-chain, ledger invariants, the kill switch — but no way for an
operator to *see* them or be alerted. There is no centralized realtime health view, no per-business
health, and no integration with the operator's monitoring system (Nagios/Icinga2). As the skeleton
runs from one business to many, this is the gap between "the controls exist" and "an operator can
watch them".

## Solution

A new `ab_monitor` bounded context that turns the skeleton's existing deterministic signals into
**Nagios plugin check results** (status + output + perfdata), tagged by `business_id`, and exports
them through a `NagiosExporter` port (stub by default; real NSCA / Icinga2-REST adapters behind it).
It reuses `ab_ops` (SLO burn) and `ab_obs` (business health) rather than reinventing them. A
docker-compose monitoring profile and the modern observability stack (Prometheus / OpenTelemetry /
Grafana / Alertmanager) are planned as **deferred infra phases** on top of the same checks.

## User Stories

1. As an operator, I want each core service's liveness (`/health`) surfaced as a Nagios check, so a
   down service pages me.
2. As an operator, I want mTLS certificate expiry as a check with warn/critical day thresholds, so a
   cert never silently lapses in the mesh.
3. As an on-call, I want SLO **error-budget burn rate** (from `ab_ops`) as a check, so I'm alerted on
   real budget burn rather than raw CPU thresholds (low alert fatigue).
4. As an operator, I want the ledger invariant (`trial_balance() == 0`) and the audit hash-chain
   integrity as CRITICAL checks, so any money/audit corruption pages immediately.
5. As a security operator, I want the kill-switch status (and last-triggered reason) as a check, so
   the halt state is visible.
6. As a portfolio operator, I want per-`business_id` health checks derived from `ab_obs` (anomalies:
   LLM-cost-high, operating-loss) so a bleeding business shows up in monitoring, not just finance.
7. As a compliance operator, I want the DSAR backlog age as a check, so an overdue erasure request
   pages before it breaches the statutory deadline.
8. As an operator, I want every check result rendered in the **Nagios plugin protocol** (exit
   status + output + perfdata) so Nagios Core, Icinga2, or Naemon all consume it unchanged.
9. As an operator, I want checks submitted to my monitoring system via a swappable adapter (NSCA /
   Icinga2 REST), so I can point the same checks at whichever I run.
10. As a developer, I want the whole check suite to run in CI on stubs (no infra), so monitoring
    logic is verified deterministically and a real submit adapter is a drop-in.
11. As an operator (later), I want the services instrumented with OpenTelemetry and scraped by
    Prometheus, with Grafana dashboards + Alertmanager routing, for metrics/traces/logs correlation.
12. As a platform owner, I want per-business checks generated dynamically from the active businesses,
    so a new business is monitored automatically.

## Implementation Decisions

- **New `src/ab_monitor/`** context (pure cores + injected port, repo pattern). `business_id` on
  every check; money in integer minor units; ratios in bps (consistent with the rest).
- **`CheckStatus`** enum: `OK=0 / WARNING=1 / CRITICAL=2 / UNKNOWN=3` (the plugin exit codes).
- **`CheckResult`** (name, status, output, perfdata: list of `Perfdatum(label, value, warn, crit)`,
  optional `business_id`) → renders to a Nagios plugin line (`STATUS: output | label=value;warn;crit`).
- **`Check` registry**: a name → evaluator map. Evaluators are pure functions over an injected
  signal (a health probe result, an `ab_ops.ErrorBudget`, an `ab_obs` snapshot/anomaly list, a
  ledger view). Reuse, don't reinvent: SLO burn = `ab_ops`; business health = `ab_obs`; invariants =
  ledger/audit/killswitch.
- **`NagiosExporter`** port: `export(results) -> None` (submit) with `render(results) -> str` (plugin
  text). `StubNagiosExporter` records/prints; real `NscaExporter` / `Icinga2RestExporter` behind it.
- **Deferred infra** (own issues, skip CI without infra): `docker-compose.monitoring.yml` (Nagios or
  Icinga2 + Icinga Web) consuming the exporter; then Prometheus `/metrics` on the FastAPI services +
  OpenTelemetry instrumentation; Grafana dashboards (Fleet / Service / Business / Security); SLO
  burn-rate alert rules + Alertmanager routing.

## Testing Decisions

- Good tests exercise the public surface — an evaluator's status given a signal, the plugin
  rendering, the exporter via its stub — with independent expected literals (prior art: `ab_obs`,
  `ab_ops`, `ab_ads`). Pure evaluators unit-tested infra-free in the CI suite; a `make monitor` demo
  emits the check suite in Nagios format; the compose/submit-adapter path is an integration test that
  skips fast without infra (prior art: `test_business_spend_store.py`).

## Out of Scope

Deploying/operating a real Nagios/Icinga2/Prometheus/Grafana/Loki/Tempo stack (the compose profile +
adapters are provided; running them is the operator's); ML-based anomaly detection; PagerDuty/Slack
account setup; log shipping (Loki/Vector) beyond the structured logs that already exist.

## Further Notes

Sliced in `.scratch/monitoring/` and (later) built via `/tdd`, one behaviour at a time. This PRD is
the plan the owner requested — the near-term slices are CI-runnable; the observability stack is
phased behind them, reusing the same deterministic checks.
