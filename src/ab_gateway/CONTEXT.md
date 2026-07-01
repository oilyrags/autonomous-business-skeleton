# Gateway

The single governed ingress for all agent tool use: it authenticates the caller, checks policy, enforces the determinism boundary and egress rules, gates money and LLM spend, and routes model access.

## Language

**Tool Registry**:
The set of governed capabilities the gateway may dispatch; an unregistered tool is uncallable, and each carries a side-effect class + sensitivity.
_Avoid_: tool list, plugin registry

**Guardrail**:
A hard pre/post condition enforced outside the LLM (policy engine, validators) that an agent cannot override.
_Avoid_: rule, check, constraint (when you mean the enforced kind)

**Model Gateway**:
The single ingress all model access routes through; maps a task profile to a promoted model + a deterministic fallback (never a best-guess).
_Avoid_: LLM client, proxy, router (informally)

**LLM Budget**:
The per-business inference budget the gateway enforces before a model call, metering spend to `{business_id}:llm_spend`.
_Avoid_: token limit, quota

**Egress**:
Transmitting data outside the trust boundary; a tool may not transmit data classified above its clearance (exfiltration control).
_Avoid_: output, send

**Decision Record**:
The immutable record of a material decision an agent made (persisted via the decision registry; emits `AgentDecisionMade`, scoped by business_id).
_Avoid_: ADR (an ADR is an architecture decision specifically), note, log entry
