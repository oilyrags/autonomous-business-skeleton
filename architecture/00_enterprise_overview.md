# 00 — Enterprise Overview

**Execution mode:** B — Build Specification.
**Document set version:** 1.0
**Date:** 2026-06-30

## 1. What this is

This package defines the *operating system of an AI-run business*: a reusable, domain-driven skeleton on which many distinct business ideas can be launched, operated, learned from, scaled, pivoted, or shut down without rebuilding the foundation. It is not a SaaS product blueprint. It is the control plane, data fabric, agent platform, and governance model that any venture plugs into.

The skeleton is **AI-first** (accountable agents run standard business functions), **open-source-preferred**, **privacy-preserving** (GDPR-first), **audit-ready**, and **deterministic where it must be** (money, identity, access, consent, irreversible actions).

> We do **not** claim architecture guarantees legal compliance. We design for **provable compliance readiness**: automated controls, evidence stores, audit logs, legal-review gates, DPIAs, DSAR workflows, policy-as-code, and jurisdiction-specific configuration.

## 2. Scope assumptions (declared, not silent)

| Dimension | Decision for v1.0 |
|---|---|
| Target company stage | **Configurable**, but defaults tuned for **startup → SMB**, designed to scale to portfolio company. |
| Target first market | **Configurable**; worked example is **B2B SaaS**. Marketplace/B2C/fintech/health enabled via compliance packs. |
| Primary regulatory baseline | **GDPR-first** (EU). |
| Optional compliance packs | finance (SOX-lite/PCI-adjacent), health (HIPAA/EU health), employment, public sector, children, payments, insurance. Off by default. |
| Deployment posture | **Configurable**; default **self-hosted Kubernetes / hybrid**, with sovereign-cloud option. |
| Data sensitivity baseline | Personal data present by default (customer PII); special-category data **off** unless a pack enables it. |
| Human oversight model | **Human-on-the-loop** by default; **human-in-the-loop** for high-risk/irreversible/legally-significant/threshold-exceeding actions. |
| Initial autonomy target | Most processes start at **Level 2–3**; finance money-movement and legal commitments start at **Level 0–3** with hard caps. |

### Explicit exclusions from v1.0
- Full implementation of every regulated industry (only GDPR + finance core; other packs are stubs).
- Level 5 autonomy for any money-moving, legally-binding, or irreversible process.
- Multi-region active-active data residency automation (single primary region + documented transfer controls only).
- Native mobile clients, on-device models, and edge inference.
- Procurement of third-party data brokers (lawful-basis risk).

## 3. The skeleton in one diagram (conceptual layers)

```
┌─────────────────────────────────────────────────────────────────────┐
│  GOVERNANCE PLANE  Decision OS · Autonomy Authority Matrix · Audit    │
│                     Kill Switch · Policy-as-Code (OPA/Cedar)          │
├─────────────────────────────────────────────────────────────────────┤
│  AGENTIC C-SUITE   CEO COO CFO CTO CPO CMO CRO CCO CDO CISO CLO CHRO  │
├─────────────────────────────────────────────────────────────────────┤
│  DOMAIN AGENTS  (16 bounded contexts, each with its own agent roster) │
│  Product · QA · CRM/Mktg · Sales · Finance · CS · Data · Compliance · │
│  Security · AI-Platform · Knowledge · Workflow · Growth · Vendor ·    │
│  People · Executive                                                   │
├─────────────────────────────────────────────────────────────────────┤
│  AGENT PLATFORM   Model Gateway · Tool Registry · Agent Identity ·    │
│                   Memory · Evals · Tracing (Langfuse/OTel)            │
├─────────────────────────────────────────────────────────────────────┤
│  INTEGRATION      Event Backbone (Kafka/Redpanda) · APIs (REST/gRPC/  │
│                   AsyncAPI) · Durable Workflows (Temporal)            │
├─────────────────────────────────────────────────────────────────────┤
│  DATA FABRIC      Lakehouse (Iceberg) · Semantic Layer (Cube) ·       │
│                   Vector (Qdrant) · Knowledge Graph · Catalog/Lineage │
├─────────────────────────────────────────────────────────────────────┤
│  PLATFORM         K8s · OpenTofu · GitOps · Keycloak/Vault · OTel     │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. Operating doctrine (binding on all agents and artifacts)

1. **Ubiquitous language is law.** One glossary (`02`). Cross-context translation goes through an anti-corruption layer (ACL).
2. **Each bounded context owns its data.** No context reads another's private store. Integration = published API or async domain event only.
3. **Every domain event** has schema, producer, consumers, retention, privacy classification, audit flag, failure handling (`04`, `events.asyncapi.yaml`).
4. **Every agent** has identity, charter, tools, permissions, KPIs, authority level, guardrails, escalation, model binding, audit hooks, kill-switch behavior (`05`).
5. **Every material decision** has evidence, decision record, framework, expected value, risk, dissent, owner, review date, learning loop (`13`).
6. **LLMs reason; deterministic systems execute.** Calculations, ledger changes, permissions, policy enforcement, contractual gates, and money movement are never left to LLM free-reasoning.
7. **Compliance/privacy/security/accessibility/auditability are design inputs**, gating release.
8. **Citations must be real.** No fabricated sources or numbers.

## 5. How the artifacts fit together

| Artifact | Role |
|---|---|
| `00_enterprise_overview.md` | This file — framing, scope, doctrine. |
| `01_context_map.mermaid` | The 16 bounded contexts and their relationships. |
| `02_ubiquitous_glossary.md` | Single source of language. |
| `03_domain_catalog.md` | Full DDD model per context. |
| `04_event_catalog.md` + `events.asyncapi.yaml` | The event backbone. |
| `05_agent_registry.json` | Every agent as a machine-readable principal. |
| `06_autonomy_authority_matrix.md` | What each process may do, at what level, under what control. |
| `07_data_model.md` + `08_data_inventory_template.json` | Canonical entities + privacy inventory. |
| `09_compliance_architecture.md` | GDPR/DSAR/DPIA/consent by construction. |
| `10_security_architecture.md` | Zero-trust, agent identity, kill switch, prompt-injection defense. |
| `11_model_and_agent_architecture.md` | Model gateway, agent runtime, evals, RAG grounding. |
| `12_tech_stack.md` | Open-source-first selections with exit paths. |
| `13_decision_operating_system.md` | Decision registry, cadences, frameworks. |
| `14_instantiation_guide.md` | How a new venture is launched on the skeleton (worked example). |
| `15_implementation_roadmap.md` | Phased build + backlog. |
| `16_verification_report.md` | Adversarial audit results + remediations. |
| `business_skeleton.md` | The Minimum Viable Autonomous Business Skeleton + deferrals. |

## 6. Success definition

The skeleton is successful when a new business idea can run end-to-end — **Build → Market → Sell → Bill → Serve → Learn** — using only defined systems and explicit approval paths, with every personal-data flow inventoried, every money-moving action capped and maker-checked, every agent action authenticated/authorized/logged/revocable, and a working kill switch. `14` proves this with a worked example; `16` audits it.
