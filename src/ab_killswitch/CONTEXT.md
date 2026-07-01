# Kill Switch

The control plane that can stop agents acting — revoking credentials and halting tool execution within an SLA, globally or scoped.

## Language

**Kill Switch**:
A control that revokes agent credentials and halts tool execution within an SLA; scope is global, per-context, or per-agent.
_Avoid_: stop button, circuit breaker (a circuit breaker is the narrower auto-trip control)

**Scope**:
The blast radius of a kill-switch activation: `global`, `context`, or `agent`.
_Avoid_: level, target (a target_id names the agent/context)

**Revocation**:
Marking a principal's credentials invalid so the gateway refuses its calls thereafter.
_Avoid_: ban, block
