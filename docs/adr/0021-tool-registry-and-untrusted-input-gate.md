---
status: accepted
---

# Tool registry + untrusted-input fail-closed

The next agent-platform component after the model gateway (architecture/11 §2): a governed
tool registry where every capability carries a contract, plus a prompt-injection defense —
sensitive tools fail closed when the agent is acting on untrusted content (architecture/10).

## Decisions

- **Tools carry contracts.** `tools.py` becomes a `REGISTRY` of `ToolSpec`s
  (`name, handler, side_effect ∈ {read,write,irreversible}, sensitive, description`) instead
  of a bare name→handler dict. Unregistered tools stay uncallable.
- **Untrusted-input gate (defense in depth).** `ToolCallRequest` gains
  `untrusted_input: bool = False`. In `/tool-call`, after authentication → revocation →
  kill-switch → OPA authorize, a sensitive tool is **refused when `untrusted_input` is set**,
  *even though policy allowed it* — `tools.blocked_by_input_trust`. The denial is audited and
  the tool never runs. This is the "sensitive tools fail closed under untrusted-input flows"
  control from §10, wired as an independent layer so a prompt-injected flow can't reach a
  write/irreversible tool.
- **Default is trusted.** `untrusted_input=False` preserves the existing happy path; a caller
  that is processing external/untrusted content (an inbound email, a fetched web page) sets it
  true. The control is *the fail-closed behaviour when it is set*, not a new default.
- **Discovery.** `GET /tools` advertises the catalog (name + contract). Authorization is still
  enforced per call (OPA + the untrusted-input gate); discovery only lists what exists.

## Verified

- Infra-free tests (+5): the registered tool has its contract; unregistered → uncallable;
  `blocked_by_input_trust` (sensitive+untrusted → blocked, sensitive+trusted → allowed,
  non-sensitive+untrusted → allowed); `/tools` lists the contract.
- Integration (against `make up-infra`, +2): a `decision_registry.write` on an
  `untrusted_input=true` flow → **403 "sensitive tool blocked under untrusted-input flow", the
  decision is never persisted, the denial is audited, the hash chain stays intact**; the same
  write on a trusted flow → 200 and persisted. Full gateway suite (24 tests: happy path, deny,
  revocation, kill-switch) still green — the refactor is behaviour-preserving. lint + mypy
  strict clean.

## Audit impact

Contributes to verification **Audit 6 (security)** — the prompt-injection control now has a
build proof (untrusted-input flow cannot reach a sensitive tool). Audit 6 stays CONDITIONAL
until the full injection + exfiltration suites are in place.

## Deferred

Principal-scoped tool *injection* (only surface tools the principal is OPA-authorized for);
per-tool required authority-level vs the agent's authority; input/output JSON-schema contracts
per tool; exfiltration controls; a richer tool catalog beyond the single write tool.
