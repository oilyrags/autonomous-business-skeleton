# 02 — Unauthorized tool call is denied and audited

Status: ready-for-agent

## What to build

The negative authorization path. An authenticated agent calls the gateway for a tool that the OPA policy does **not** grant (anything other than `decision_registry.write` for the skeleton principal). OPA returns deny (default-deny), the gateway rejects with a 403-equivalent and a reason, no tool runs, no `Decision` is written, and the denial is recorded as an audit event.

## Acceptance criteria

- [ ] A call to an unapproved tool returns a denial with a reason and performs no side effect (no Decision, no domain event).
- [ ] OPA returned deny by default (the policy grants only the one approved action).
- [ ] The denial produces an immutable audit record (the chain still verifies).

## Blocked by

- 01 — Happy-path tracer
