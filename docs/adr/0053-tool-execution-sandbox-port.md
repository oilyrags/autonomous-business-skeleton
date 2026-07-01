---
status: accepted
---

# Tool execution sandbox port

Closes the P2 "tool execution sandboxing (E2B/Modal-style) + full audit of every tool invocation"
gap: the port + a policy-enforcing stub + the audit guarantee. A real isolation backend slots in
behind the same interface. PRD 0003; pure.

## Decisions

- **New `ab_sandbox` context.** A `SandboxPolicy` is a capability allow-list (`Capability` ∈
  network / filesystem / subprocess / env). `evaluate(invocation, policy)` is **deny-by-default**: a
  tool is permitted only if *every* capability it requests is on the allow-list; otherwise denied
  with the offending capabilities named — the decision an adapter enforces before running anything.
- **Sandbox is a port** (`Sandbox.execute(invocation) -> SandboxDecision`); `StubSandbox` enforces
  the policy without real isolation and **audits every invocation** (permitted or denied). An
  E2B/Modal adapter implements the same `execute` with true process isolation.

## Verified

4 pure tests (within policy permitted; out-of-policy capability denied + named; empty policy permits
nothing; every invocation audited). `make sandbox` (in CI): permits network/filesystem tools, denies
subprocess/env, audits all four. Full suite 234 passed, 36 skipped; ruff + mypy strict clean (111
files).

## Deferred

A real E2B/Modal isolation adapter; resource limits (wall-clock/memory) enforcement; wiring the
sandbox into the gateway's tool-dispatch path so every real tool call routes through it.
