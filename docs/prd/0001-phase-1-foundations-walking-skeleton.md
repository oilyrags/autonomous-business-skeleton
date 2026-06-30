# PRD 0001 — Phase 1 Foundations: Walking Skeleton

> **Triage label:** `ready-for-agent`
> **Status:** drafted, pending publish to GitHub Issues (the configured tracker; requires `gh`, not yet installed — see Further Notes).
> **Source:** grill-with-docs session, 2026-06-30 (12 resolved decisions). Related: ADR-0001, ADR-0002, ADR-0003; roadmap `architecture/15_implementation_roadmap.md` Phase 1; security `architecture/10_security_architecture.md`.

## Problem Statement

We have a complete v1.0 architecture (16 contexts, 72 agents, events, controls) but **zero running code**. There is no proof that the foundational guarantees the whole design rests on — *every agent action is authenticated, authorized, logged, and revocable, and a kill switch actually halts agents* — can be built and hold together. Until that spine exists and is exercised end-to-end, every later phase is built on an unproven foundation.

## Solution

Build a **walking skeleton**: the thinnest end-to-end vertical slice that exercises identity, authorization, audit, events, and the kill switch at once. A single agent principal, through the model gateway, makes **one** OPA-authorized, audit-logged tool call — `decision_registry.write` — that records a `Decision` and emits `AgentDecisionMade` on the event bus; an audit consumer records receipt; and the **kill switch can halt the agent's next call within an SLA**. Everything later grows from this spine; the interfaces are real even where the implementations are interim.

## User Stories

1. As a platform operator, I want every agent to authenticate with a verifiable identity before acting, so that no anonymous action is possible.
2. As a platform operator, I want each agent's identity to be short-lived and revocable, so that I can cut off a compromised or misbehaving agent.
3. As a security owner, I want every tool call gated by a default-deny policy decision, so that an agent can only do what it is explicitly authorized to do.
4. As a security owner, I want an agent calling an unapproved tool to be denied and the denial recorded, so that policy violations are visible.
5. As an auditor, I want every tool call to produce an immutable, tamper-evident audit record, so that I can reconstruct exactly what happened and prove the log was not altered.
6. As an auditor, I want to read the audit log through a query API, so that I can inspect activity without touching the store directly.
7. As an operator, I want the agent's reasoning to go through a model gateway, so that the model is a swappable component and money/legal/irreversible logic never depends on free-form model output.
8. As an operator, I want the skeleton's model to be a deterministic stub, so that the slice runs offline, fast, and reproducibly.
9. As an agent, I want to record a Decision via a registered tool, so that a material decision is captured with provenance.
10. As a downstream consumer, I want `AgentDecisionMade` published on the event bus when a decision is recorded, so that other contexts can react asynchronously.
11. As a security owner, I want to activate a kill switch globally or for a single agent, so that I can stop action at the right blast radius.
12. As a security owner, I want an activated kill switch to deny the agent's next tool call within a defined SLA, so that the control is fast enough to matter.
13. As a security owner, I want kill-switch activation to revoke the agent's token AND set a control flag the gateway checks, so that the halt does not depend solely on token expiry.
14. As a security owner, I want kill-switch activation itself recorded (audit + `KillSwitchActivated` event), so that use of the control is evidenced.
15. As an operator, I want the whole stack to come up locally with one command, so that any contributor (or agent) can run and test it.
16. As a developer, I want the acceptance criteria expressed as automated tests run in CI, so that the foundation's guarantees are continuously verified.
17. As a developer, I want lint, type-check, and tests to gate every change, so that feedback is fast and regressions are caught.
18. As a maintainer, I want the agent to be a separate authenticated principal calling the gateway over the wire, so that the trust boundary between agent and platform is real, not in-process.

## Implementation Decisions

**Architectural shape** (ADR-0001/0002): Python monorepo under `src/` in this repo. Five services as Python packages + a shared schema lib, wired via HTTP + Redpanda + Postgres, orchestrated by docker-compose.

**Services / modules:**
- `identity` — issues short-lived signed JWTs for agent principals; validates; maintains a revocation list. Interim custom issuer (ADR-0003); Keycloak/SPIFFE deferred. Kept **outside** the gateway so revocation is independently trustworthy.
- `gateway` — the single ingress. Validates the principal's token, routes the task profile to a (stub) model, dispatches the registered tool call, calls OPA to authorize, checks kill-switch state, emits the audit event and the domain event. Determinism boundary lives here.
- `killswitch` — holds control flags (global / per-agent), drives token revocation via `identity`, publishes `KillSwitchActivated`. The launch-blocker control.
- `audit` — append-only, hash-chained writer (each row hash-links the previous, tamper-evident) in Postgres; exposes a read API; also consumes `AgentDecisionMade` to record receipt.
- `agent` — the runtime: perceive → reason via gateway → act. Holds an identity, makes the one tool call.
- shared `schemas` lib — Pydantic models matching `architecture/events.asyncapi.yaml` (envelope + `AgentDecisionMade` + `KillSwitchActivated`).

**Infra (containers):** OPA (sidecar, REST `authz/evaluate`, default-deny Rego), Redpanda (single node, Kafka API), Postgres (audit + decision rows).

**Key interfaces (shape, not file paths):**
- `gateway`: `POST /tool-call { principal_token, tool, args, purpose }` → authorized result or `403` with reason; always writes an audit record first-class.
- OPA input: `{ principal, action, resource, purpose }` → `{ allow: bool, reason }`; default-deny.
- `identity`: issue / validate / `POST /revoke {agent_id}`.
- `killswitch`: `POST /activate { scope: global|agent, target_id?, reason }`, `GET /state`.
- `audit`: append (internal) + `GET /audit?...`; each record carries `prev_hash`, `hash`.
- Events: `AgentDecisionMade`, `KillSwitchActivated` on Redpanda, envelope per AsyncAPI.

**Authorization:** real OPA from slice one; default-deny; the skeleton policy grants exactly `decision_registry.write` to the skeleton agent principal and nothing else.

**Determinism boundary:** the gateway is real; the skeleton task profile binds to a deterministic stub model. Recording the Decision and emitting the event are deterministic code paths, never model-driven.

## Testing Decisions

**What makes a good test here:** exercise behaviour through public interfaces (the gateway HTTP API, the audit read API, the event bus) — never internal functions or DB rows directly except to assert the tamper-evident chain. Tests read like the acceptance criteria. TDD red-green-refactor (pytest); integration-style against the real stack via docker-compose (or testcontainers).

**The single highest seam is the `gateway` tool-call API.** Drive all behaviour through it; observe through the `audit` read API and a test consumer on the bus. This keeps the seam count near one.

**Acceptance tests (the spec):**
1. An agent **cannot** call an unapproved tool → `gateway` returns deny + an audit record of the denial exists.
2. A **revoked** agent token fails immediately → after `identity`/`killswitch` revoke, the next `gateway` call is rejected.
3. **Every** tool call creates an immutable audit record → assert the record exists and the hash-chain links verify (tamper-evidence).
4. Recording a Decision **emits `AgentDecisionMade`** → a test consumer on Redpanda receives it; `audit` records receipt.
5. **Kill switch drill** → activate (global, then per-agent); the agent's next `gateway` call is denied **within the SLA**; `KillSwitchActivated` is published and audited.

**Prior art:** none yet (first code). These tests establish the pattern for the repo.

## Out of Scope

- Real IdP (Keycloak/Zitadel) and SPIFFE/mTLS — deferred (ADR-0003).
- Real model providers (vLLM/managed) — stub only this slice.
- Human OIDC login, RBAC/ABAC beyond the one skeleton policy, secrets manager (Vault), per-context kill-switch scope.
- Tool registry UI, multiple tools, multiple agents, multiple events.
- Data inventory / personal-data / DSAR paths (the action is non-personal).
- Production deployment, Kubernetes, GitOps (local docker-compose + minimal GitHub Actions only).
- Semantic layer, lakehouse, and everything in roadmap Phases 2+.

## Further Notes

- **Publishing:** the configured tracker is GitHub Issues, but `gh` is not installed in the environment. This PRD lives as a repo file for now; once `gh` is available it should be published as a GitHub issue with the `ready-for-agent` label, and `/to-issues` run to slice it into vertical-slice issues.
- **Conventions:** uv (deps/venv), ruff (lint/format), mypy strict, pytest, docker-compose + Makefile (`make up`, `make test`), GitHub Actions CI (lint + type-check + tests).
- **Decomposition into issues (preview for `/to-issues`):** each acceptance test is a candidate vertical slice — (a) identity issue/validate + agent authenticates through gateway; (b) OPA authorize + deny path; (c) audit hash-chain + read API; (d) Decision write + `AgentDecisionMade` + consumer; (e) kill-switch activate + revoke + fail-closed drill. Plus a slice-0 for repo/compose/CI scaffolding.
