# M3 — Per-business health checks (multi-tenant)

**Parent:** PRD 0005 / ADR-0055. **Triage:** ready-for-agent.

## What to build

Per-`business_id` health checks so a struggling business shows up in monitoring, not just finance.
**Reuse `ab_obs`** — map its anomalies to check statuses rather than reinventing:
- An `ab_obs` `OPERATING_LOSS` anomaly → CRITICAL for that business; `LLM_COST_HIGH` → WARNING.
- A healthy business → OK. Perfdata carries `operating_profit`, `llm_cost_ratio_bps`.
- **DSAR backlog age** → WARNING/CRITICAL as the oldest open request approaches the statutory
  deadline (reuse the compliance signal).

Generate one set of checks **per active business** (dynamic), each `CheckResult` tagged with its
`business_id`, so a newly-activated business is monitored automatically.

## Acceptance criteria

- [ ] A pure `business_checks(snapshots/anomalies) -> list[CheckResult]` that maps `ab_obs` anomalies
      to statuses, each tagged with `business_id`, with perfdata.
- [ ] DSAR-backlog evaluator: age under threshold → OK, approaching deadline → WARNING, over →
      CRITICAL.
- [ ] Per-business generation over a set of businesses produces one tagged result-set each; a healthy
      fleet → all OK. Unit-tested with independent literals; included in `make monitor`.
- [ ] ruff + mypy strict clean.

## Blocked by

- M1 (the `CheckResult` model + registry + exporter).
