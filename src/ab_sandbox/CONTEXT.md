# Sandbox

Runs tool code under a capability policy: deny-by-default, and every invocation is audited. A real E2B/Modal isolator slots in behind the port.

## Language

**Capability**:
A privilege a tool may need (`network`, `filesystem`, `subprocess`, `env`); granted only if on the policy allow-list.
_Avoid_: permission, scope (a Scope is the kill-switch blast radius)

**Sandbox Policy**:
The allow-list of capabilities a tool may use; anything outside it is refused before execution (deny-by-default).
_Avoid_: ruleset, config
