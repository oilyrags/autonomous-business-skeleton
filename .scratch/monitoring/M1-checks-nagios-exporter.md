# M1 — ab_monitor tracer bullet: checks + Nagios exporter

**Parent:** PRD 0005 / ADR-0055. **Triage:** ready-for-agent.

## What to build

The thin end-to-end path of `ab_monitor`: evaluate a few deterministic checks and export them in the
vendor-neutral Nagios plugin protocol. A `CheckStatus` (OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3), a
`CheckResult` (name, status, output, `perfdata`, optional `business_id`) that renders to a Nagios
plugin line (`STATUS: output | label=value;warn;crit`), and a check registry mapping name → pure
evaluator. Seed evaluators that **reuse existing signals**: service liveness (from an injected health
probe result), mTLS certificate expiry (days → warn/crit thresholds), and SLO error-budget burn
(reusing `ab_ops.ErrorBudget`). A `NagiosExporter` port with a `StubNagiosExporter` (records/renders,
no infra). `make monitor` runs the suite and prints the Nagios-format results.

## Acceptance criteria

- [ ] `CheckStatus` maps to plugin exit codes 0/1/2/3; `CheckResult.render()` emits
      `STATUS: output | perfdata` in valid Nagios plugin format.
- [ ] `Perfdatum(label, value, warn, crit)` renders as `label=value;warn;crit`.
- [ ] Evaluators (pure): service-up (down health → CRITICAL), mTLS expiry (≤crit days → CRITICAL,
      ≤warn → WARNING, else OK), SLO burn via `ab_ops.ErrorBudget` (over-budget → CRITICAL) — each
      with independent-literal tests.
- [ ] `NagiosExporter` port + `StubNagiosExporter`; `export(results)` records what would be submitted.
- [ ] `make monitor` (in CI) evaluates the suite and prints Nagios-format lines. ruff + mypy strict
      clean; unique test basenames.
- [ ] `src/ab_monitor/CONTEXT.md` created (glossary from ADR-0055) and linked from `CONTEXT-MAP.md`.

## Blocked by

None — can start immediately.
