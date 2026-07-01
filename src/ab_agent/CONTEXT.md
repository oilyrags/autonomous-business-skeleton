# Agent

The runtime for an accountable AI actor — the identity-bearing entity that proposes actions, which the gateway then governs.

## Language

**Agent**:
An accountable, identity-bearing AI actor with a charter, tools, permissions, authority level, and audit hooks.
_Avoid_: bot, assistant, script

**Tool Call**:
An agent's request to invoke a governed capability, carrying purpose and untrusted-input flag; dispatched only through the gateway.
_Avoid_: action, command (when you mean the governed request)
