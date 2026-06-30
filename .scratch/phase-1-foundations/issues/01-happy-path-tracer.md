# 01 — Happy-path tracer: authenticated agent records a Decision end-to-end

Status: ready-for-agent

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
