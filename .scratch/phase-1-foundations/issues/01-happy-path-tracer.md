# 01 — Happy-path tracer: authenticated agent records a Decision end-to-end

Status: done

## What to build

The tracer bullet through every layer. The `agent` obtains a short-lived signed JWT from `identity` and calls the `gateway` tool-call API to invoke `decision_registry.write`. The `gateway` validates the token, routes the (stub) model task profile, asks OPA to authorize `{principal, action: decision_registry.write, resource, purpose}` (policy allows it), dispatches the tool which persists a `Decision` row, writes a hash-chained audit record, and publishes `AgentDecisionMade` to Redpanda. The `audit` service consumes `AgentDecisionMade` and records receipt; its read API returns the audit trail.

This proves identity + gateway + OPA(allow) + tool + persistence + audit(hash chain) + events all hold together. Drive the test through the gateway API; observe via the audit read API and a test consumer on the bus (the confirmed single highest seam).

## Acceptance criteria

- [ ] An authenticated agent call to `decision_registry.write` via the gateway returns success and persists exactly one `Decision`.
- [ ] OPA is consulted on the call and returns allow; the decision path never computes anything via the model (determinism boundary).
- [ ] Exactly one immutable audit record is written for the call, and the hash chain verifies (each row links the previous).
- [ ] `AgentDecisionMade` is published with the AsyncAPI envelope and received by a test consumer; the `audit` service records receipt.
- [ ] The audit read API returns the call's record(s).

## Blocked by

- 00 — Scaffold

## Comments

**Done (2026-06-30).** Implemented + verified end-to-end against the live stack; all acceptance criteria pass (`test_agent_records_decision_end_to_end`). `make check` green: ruff + mypy(strict, 23 files) + pytest (3 passed).

Built: `ab_identity` (HS256 JWT issue/validate), `ab_gateway` (`POST /tool-call`: token → kill-switch hook → stub model → OPA allow → tool dispatch → audit → emit), `ab_audit` (hash-chained store + read API + `AgentDecisionMade` consumer), `decision_registry.write` tool, `ab_agent` runtime, `ab_common` (config/db/bus), OPA allow rule. Test drives the gateway seam; observes via audit store + a seek-to-end Redpanda consumer.

Deviations / decisions (carry forward):
- **Ports remapped** to dodge a developer's local services: Postgres host **55432**, Redpanda external listener **19092** (dual listeners: internal `redpanda:9092` for in-container, external `localhost:19092` for host). OPA stays 8181.
- **Services run in-process** (FastAPI apps via TestClient) against real OPA/Redpanda/Postgres for tests. Containerizing the 5 services (Dockerfiles + uvicorn in compose, replacing the `sleep` placeholders) is deferred to a deploy slice.
- Kill-switch check is wired into the gateway but stubbed `is_killed -> False` (slice 04 makes it real).
- CI now boots the compose infra and runs the integration test.

