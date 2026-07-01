---
status: accepted
---

# Reliability: error budget + auto-rollback — failure-injection suite now 7/7

The last DEFERRED failure-injection scenario (incident/rollback) becomes build-proven with a
new `ab_ops` (Reliability/SRE) context — so the whole suite is now CONTAINED.

## Decisions

- **`ab_ops.reliability`** — deterministic, no I/O, no wall-clock:
  - `ErrorBudget(slo_target, window)` → `budget = (1 - slo) * window`; `exhausted(errors)`.
  - `ReleaseManager(current, previous, frozen)` → `deploy` (raises `ReleaseFrozen` when frozen),
    `rollback` (reverts to the last good version; raises `NothingToRollBackTo` if none),
    `freeze`, `can_release(budget, errors)`.
  - `handle_incident(incident, release, budget, errors)` contains an incident: **Sev1 →
    auto-rollback + freeze**; error-budget burn → freeze; Sev1/Sev2 → postmortem required;
    PII touched → breach assessment (GDPR Art.33/34).
- **`ab_failsim`'s incident scenario now runs the real control:** a Sev1 during a `v2-bad`
  release that touched PII → the release rolls back to `v1`, further deploys are frozen,
  a postmortem and a PII breach assessment are required → CONTAINED.

## Verified

- `make failsim` → **7 contained, 0 breach, 0 deferred** — the failure-injection suite is fully
  build-proven. Tests (+8): error-budget math; deploy→rollback; deploy blocked while frozen;
  rollback with no previous raises; `can_release` under freeze/budget; Sev1+PII auto-rollback +
  freeze + breach; Sev3 no-op; budget-exhaustion freeze without a Sev1. lint + mypy strict clean.

## Deferred

Wiring the release manager to a real deploy pipeline / CD; persisting incidents + postmortems;
an actual breach-notification workflow (Art.33 72-hour clock); burn-rate alerting.
