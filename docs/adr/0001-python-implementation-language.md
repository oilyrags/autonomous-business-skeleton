# Implementation language is Python

The platform and agent services are built in **Python**. The agent/LLM ecosystem the roadmap depends on — LangGraph, OpenAI-compatible gateways (LiteLLM-style), vLLM, eval harnesses — is Python-first, so a single language minimises friction across the walking skeleton and the contexts that follow.

## Considered Options

- **Python** (chosen) — native to the AI/agent ecosystem; one language for the whole skeleton.
- **TypeScript** — single language across a future web UI + services and aligns with the vendored skills' TS lean, but a thinner AI ecosystem.
- **Go** — best for security/platform plumbing (SPIFFE, OPA are Go-native), but would split the codebase across two languages this early.

## Consequences

Go remains a deliberate option for later hot-path platform services; introducing it now would be premature. Service interfaces (HTTP + events) are kept language-agnostic so a future Go service can slot in behind the same contracts.
