# 04 — Kill switch halts the agent within an SLA (drill)

Status: done

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

## Comments

**Done (2026-06-30).** `ab_killswitch` real now: `control.activate(scope, target_id, …)` sets a Postgres control flag, revokes the principal on agent scope (defence in depth), audits the activation, and publishes `KillSwitchActivated`. `state.is_killed` reads the flags; the gateway checks it on every call and **fails closed** (any read error → deny). Tests: global kill denies the next call within a 2s SLA + event published + audited; per-agent kill is scoped (other agents unaffected, target denied); fail-closed on unreadable state (monkeypatched); audit-tamper (`UPDATE` one row) makes `verify_chain()` return False. Full suite: ruff + mypy(26 files) + 11 tests green.
