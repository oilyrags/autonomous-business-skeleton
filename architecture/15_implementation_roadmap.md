# 15 — Implementation Roadmap & Backlog

Pragmatic, phased build. Each phase: goals, deliverables, dependencies, risks, team, complexity, success metrics, validation. Backlog-ready stories follow, each mapped to artifacts, contexts, verification checks, the authority matrix (for agent actions), and data inventory/lawful basis (for personal data).

## Phase overview

| # | Phase | Goal | Complexity | Success metric |
|---|---|---|---|---|
| 1 | Foundations | Identity, audit log, event backbone, policy engine, repo standards, **kill switch** | M | every action authenticated+logged; kill switch drilled |
| 2 | Core data | Canonical model, data inventory, data contracts, semantic layer | M | 1 definition/KPI; PII classified at ingestion |
| 3 | Agent platform | Model gateway, tool registry, agent identity, memory, evals, tracing | L | all model calls via gateway; eval gate enforced |
| 4 | Product factory | Specs, CI/CD, QA, release automation | M | DORA baseline; no-green-no-ship enforced |
| 5 | CRM/Sales/Support | Consent, campaigns, CPQ, grounded support | L | lawful-basis enforced; grounded-answer rate |
| 6 | Finance & compliance | Ledger, billing, DSAR, DPIA, evidence store | L | maker-checker on money; DSAR saga complete |
| 7 | C-suite & Decision OS | Agentic C-suite, decision registry, cadences | M | decisions cite data+framework; review loop runs |
| 8 | Portfolio operation | Multi-venture instantiation pipeline | M | 2nd venture launches without skeleton changes |
| 9 | Continuous optimization | Red-teaming, compliance audits, drift control | M | audits pass; failure-injection remediated |

**Dependencies:** 1→all; 2→{5,6,7}; 3→{4,5,6,7}; 6 requires 1,2,3; 7 requires 2,3,6; 8 requires 4–7; 9 continuous from 3.

**Team (lean, AI-augmented):** platform/SRE, data engineer, ML/LLM engineer, security engineer, compliance/DPO (human), full-stack, + the agent fleet. Humans concentrate on approvals, legal, and oversight.

## Per-phase detail (goals · deliverables · risks · validation)

### Phase 1 — Foundations
- **Goals:** secure, auditable base. **Deliverables:** Keycloak/Zitadel, OPA, Vault, Redpanda + AsyncAPI registry, immutable audit log, GitOps repo standards, kill switch (global/context/agent). **Risks:** kill switch unproven (mitigate: drill in CI), policy sprawl. **Validation:** revoked token fails instantly; kill switch halts a test agent within SLA; every tool call → audit event.

### Phase 2 — Core data
- **Goals:** trusted data fabric. **Deliverables:** canonical model (`07`), data inventory (`08`), Iceberg lakehouse + medallion, dbt, Cube semantic layer, OpenMetadata catalog/lineage, quality tests, classification-at-ingestion. **Risks:** metric duplication. **Validation:** each seeded KPI has exactly one definition; PII auto-classified; lineage queryable.

### Phase 3 — Agent platform
- **Goals:** safe agent substrate. **Deliverables:** model gateway (task profiles + fallbacks), tool registry, agent identity, memory, eval harness + Langfuse, OTel tracing. **Risks:** hallucination, prompt injection. **Validation:** no direct vendor calls; unregistered tool uncallable; eval-gate blocks a known-bad model; injection test blocked.

### Phase 4 — Product factory
- **Goals:** autonomous software delivery. **Deliverables:** spec→ADR→codegen→review→CI/CD→progressive delivery→rollback, security/license scans, SLOs/error budgets, incident mgmt. **Risks:** flaky gates. **Validation:** DORA baseline captured; failing tests block ship; rollback drill passes.

### Phase 5 — CRM/Sales/Support
- **Goals:** lawful growth + conversion + grounded service. **Deliverables:** consent service, segments/campaigns with suppression, lead routing/CPQ/deal-desk, grounded support + escalation. **Risks:** sending to suppressed contacts, ungrounded answers. **Validation:** pre-send suppression hard-blocks; discount>threshold needs approval; ungrounded answer escalates.

### Phase 6 — Finance & compliance
- **Goals:** financial control + rights. **Deliverables:** double-entry ledger, billing/AR/AP, revrec engine, maker-checker payments + caps, DSAR saga, DPIA engine, evidence store, breach workflow. **Risks:** double-payment, incomplete erasure. **Validation:** ledger balances; payment idempotent + capped; DSAR erasure confirmed by every mapped context or itemized hold.

### Phase 7 — C-suite & Decision OS
- **Goals:** accountable autonomy. **Deliverables:** 12 C-agents, decision registry, cadences, frameworks library, learning loop. **Risks:** decisions on stale data, groupthink. **Validation:** decision blocked without provenance+framework; dissent recorded; freshness gate fires.

### Phase 8 — Portfolio operation
- **Goals:** reuse. **Deliverables:** instantiation pipeline (`14`), venture config, gate workflows. **Risks:** skeleton drift per venture. **Validation:** a 2nd venture launches using only config + idea-specific artifacts; no core changes.

### Phase 9 — Continuous optimization
- **Goals:** stay safe + compliant over time. **Deliverables:** red-team agent + scheduled human red-teaming, periodic compliance audits, drift detection, access reviews. **Risks:** regression. **Validation:** failure-injection suite (`16`) runs on schedule; findings auto-demote affected processes until fixed.

---

## Backlog (representative stories — every phase has epics/stories/tasks/AC/DoD)

### Story: Register agent identity and permission boundary
- **Phase:** Foundations · **Bounded context:** Security, Risk, and Trust
- **User outcome:** Operators can identify, authorize, revoke, and audit every agent.
- **Architecture artifacts:** `05_agent_registry.json`, `06_autonomy_authority_matrix.md`, `10_security_architecture.md`
- **Authority matrix:** AM-24/AM-25 (containment/kill) · **Data/lawful basis:** n/a
- **Tasks:** define agent principal schema; least-privilege role model; emit audit event per tool call; kill-switch revocation path.
- **Acceptance tests:** an agent cannot call an unapproved tool; a revoked token fails immediately; every tool call creates an immutable audit event.
- **Verification checks:** Security audit, Autonomy audit, Event audit.
- **DoD:** tests pass; audit event in catalog; authority matrix references the agent class.

### Story: Enforce one canonical definition per KPI
- **Phase:** Core data · **Context:** Data Platform & Intelligence
- **Outcome:** Every KPI resolves to a single semantic-layer definition.
- **Artifacts:** `07`, `12`, `13` · **Data:** metrics may aggregate personal data → access-policy enforced.
- **Tasks:** model metrics in Cube; CI check rejecting duplicate definitions; provenance on query results.
- **AC:** two definitions of the same KPI fail CI; every dashboard reads the canonical metric.
- **Verification:** Data audit. **DoD:** single-definition coverage = 100% of seeded KPIs.

### Story: DSAR erasure propagates across all personal-data contexts
- **Phase:** Finance & compliance · **Context:** Compliance, Privacy & Legal (+ all personal-data contexts)
- **Outcome:** A subject's erasure request is fulfilled and evidenced everywhere, with legal holds itemized.
- **Artifacts:** `09`, `08`, `04`, `events.asyncapi.yaml` · **Authority:** AM-16 · **Data/basis:** legal_obligation for the request; per-element basis from `08`.
- **Tasks:** implement Subject Rights API consumer in each context; DSAR saga with completeness check; legal-hold check; evidence write.
- **AC:** `DataDeletionCompleted` emitted only after every mapped context confirms; financial records retained are itemized with basis; status queryable.
- **Verification:** Compliance audit, DSAR audit, Event audit. **DoD:** end-to-end DSAR test green; evidence stored.

### Story: Money movement is capped and maker-checked
- **Phase:** Finance & compliance · **Context:** Finance + Workflow
- **Outcome:** No agent moves money beyond a pre-authorized, rules-based, approved path.
- **Artifacts:** `06` (AM-11), `03`, `10` · **Authority:** AM-11 · **Data:** financial.
- **Tasks:** spend-cap enforcement (deterministic); payee allow-list; maker-checker approval workflow; idempotency keys.
- **AC:** payment above cap blocks → `ApprovalRequired`; new payee always requires approval; duplicate payment rejected by idempotency.
- **Verification:** Finance audit, Autonomy audit, Failure-injection (bad payment). **DoD:** all tests pass; ledger balanced.

### Story: Grounded, escalating customer answers
- **Phase:** CRM/Sales/Support · **Context:** Customer Service
- **Outcome:** Answers are grounded in approved sources or escalate.
- **Artifacts:** `03`, `11`, `12` · **Authority:** AM-14 · **Data:** personal (conversation) — `support_retention`.
- **Tasks:** RAG over approved KnowledgeArtifacts; provenance + citation; abstain/escalate on low grounding; DSAR routing.
- **AC:** ungrounded query escalates; DSAR request routes to Compliance; answer cites sources.
- **Verification:** AI audit, Compliance audit. **DoD:** grounding-rate metric live; escalation path tested.

### Story: Kill switch is a verified launch blocker
- **Phase:** Foundations (+ re-verified each phase) · **Context:** Security
- **Outcome:** Global/context/agent kill switch halts agent action within SLA; deactivation is dual-control.
- **Artifacts:** `10`, `06` (AM-25) · **Authority:** AM-25.
- **Tasks:** broadcast `KillSwitchActivated`; gateway + runtime fail-closed; dual-control deactivation; drill harness.
- **AC:** activated kill switch stops a test agent's tool calls within SLA; deactivation needs two human approvals.
- **Verification:** Security audit, Failure-injection. **DoD:** drill passes; RTO measured; launch gate references it.

> Each remaining phase follows the same template (epics, stories, technical/data/compliance/security/AI tasks, AC, dependencies, risks, DoD). Deferred items are listed in `business_skeleton.md` with rationale, risk, and inclusion trigger.
