# 04 — Kill switch halts the agent within an SLA (drill)

Status: ready-for-agent

## What to build

The launch-blocker control. The `killswitch` service activates at `global` or `agent` scope: it sets a control flag the gateway checks on every tool call **and** drives token revocation via `identity`, then publishes `KillSwitchActivated`. Once activated, the agent's next gateway call is denied within a defined SLA (fail-closed). Activation is itself audited. Includes an audit-tamper test: mutating a stored audit row breaks the hash-chain verification.

## Acceptance criteria

- [ ] Activating the kill switch (global) causes the agent's next gateway call to be denied within the SLA (assert the elapsed bound).
- [ ] Per-agent activation denies only the targeted agent; other principals are unaffected.
- [ ] Activation publishes `KillSwitchActivated` and writes an audit record.
- [ ] The gateway fails closed: if kill-switch state cannot be read, calls are denied (not allowed).
- [ ] Tamper test: altering any stored audit row causes the hash-chain verification to fail.

## Blocked by

- 01 — Happy-path tracer
- 03 — Token revocation
