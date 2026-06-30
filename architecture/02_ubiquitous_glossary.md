# 02 — Ubiquitous Glossary

One glossary governs all contexts. Where a context needs a different meaning for the same word, it is marked **[ACL]** and the translation is defined. Terms are the canonical spelling used in code, events, APIs, and decision records.

## Platform & governance

| Term | Definition |
|---|---|
| **Bounded Context** | An explicit boundary inside which a domain model and its ubiquitous language are consistent. Owns its data; integrates only via API/event/ACL. |
| **Anti-Corruption Layer (ACL)** | Translation layer that maps another context's model into the local model so foreign concepts do not leak in. |
| **Agent** | An accountable, identity-bearing AI actor with a charter, tools, permissions, authority level, guardrails, and audit hooks. Not an unbounded script. |
| **Authority Level (0–5)** | The autonomy a process/agent is granted. See `06`. L0 manual … L5 self-optimizing within audited control loops. |
| **Charter** | The mission, scope, allowed actions, and constraints binding a specific agent. |
| **Guardrail** | A hard pre/post condition enforced outside the LLM (policy engine, validators) that an agent cannot override. |
| **Kill Switch** | A control that revokes an agent's (or all agents') credentials and halts tool execution within an SLA. Global and per-agent. |
| **Decision Record** | The immutable record of a material decision (`13` schema). |
| **Material Decision** | Any decision affecting money, legal exposure, personal data, customers, security, or strategy above a defined threshold. |
| **Maker-Checker** | Separation where the entity that creates an action cannot approve it. |
| **Policy-as-Code** | Authorization and compliance rules expressed as evaluable code (OPA/Cedar), versioned and tested. |
| **Provenance** | The traceable source of a fact or output, including dataset, query, and timestamp. |
| **Evidence Store** | Append-only repository of artifacts proving a control operated (logs, approvals, DPIAs, eval results). |
| **Compliance Pack** | An optional, sector-specific module adding data rules, controls, and thresholds (finance, health, etc.). |

## Customer & revenue

| Term | Definition |
|---|---|
| **Lead** | A person/organization that has shown interest but is not yet qualified. |
| **Contact** | A natural person we hold personal data about. The DSAR subject unit. |
| **Account** | An organization we sell to or serve (B2B). |
| **Customer** | An Account or Contact with at least one active or past paid relationship. |
| **Opportunity** | A qualified potential deal with a stage, value, and close date. |
| **Consent** | A lawful-basis record capturing a data subject's permission for a stated purpose, with grant/revoke timestamps. **[ACL]** Marketing treats consent as channel+purpose scoped; Finance treats lawful basis as `contract`/`legal_obligation`. |
| **Segment** | A defined cohort used for targeting/analysis; membership is derived and versioned. |
| **Subscription** | A recurring entitlement a Customer holds, driving billing and access. |
| **Entitlement** | The concrete features/limits a Customer may use, derived from Subscription/Contract. |

## Finance

| Term | Definition |
|---|---|
| **Ledger Entry** | An append-only, double-entry accounting record. Immutable. |
| **Invoice** | A demand for payment issued to a Customer; an Account Receivable. |
| **Payment** | A money movement settling (part of) an Invoice. |
| **Revenue Recognition** | Deterministic allocation of revenue to periods per policy (e.g. ratable for subscriptions). |
| **Unit Economics** | Per-unit contribution: LTV, CAC, payback, contribution margin, gross margin. |
| **Spend Cap** | A pre-authorized maximum an agent may commit without human approval. |

## Product, data & AI

| Term | Definition |
|---|---|
| **Data Product** | An owned, contracted, discoverable dataset with SLA, lineage, classification, quality tests. |
| **Data Contract** | The schema + semantics + SLA a producer guarantees to consumers. |
| **Semantic Layer / Metric** | The single canonical definition of a KPI (one definition per metric). |
| **Feature (data)** | A model input served from the feature store. **[ACL]** distinct from **Feature (product)** = a shippable capability. |
| **Release** | A versioned, reversible deployment of product changes. |
| **Incident** | A degradation/outage tracked through detection → resolution → postmortem. |
| **Model** | A versioned LLM/ML artifact accessed via the Model Gateway. |
| **Model Evaluation** | A scored test of a model/agent against a fixed eval set + guardrail checks. |
| **Task Profile** | A named routing intent (e.g. `financial_reasoning`) the gateway maps to a model + fallback. |
| **Grounding** | Constraining generation to retrieved, provenance-bearing sources. |

## Compliance & rights

| Term | Definition |
|---|---|
| **Data Subject Request (DSAR)** | A request to exercise a right: access, erasure, portability, rectification, objection, restriction. |
| **Lawful Basis** | The GDPR Art.6 ground for processing personal data: consent, contract, legitimate_interest, legal_obligation, vital_interest, public_task. |
| **RoPA** | Record of Processing Activities (GDPR Art.30), generated from the data inventory. |
| **DPIA** | Data Protection Impact Assessment, triggered for high-risk processing. |
| **Purpose Limitation** | Personal data used only for the inventoried purpose tied to its lawful basis. |
| **Legal Hold** | A suspension of erasure/retention for litigation/regulatory reasons; overrides deletion. |
| **Significant Automated Decision** | An automated decision with legal or similarly significant effect on a person (GDPR Art.22), requiring transparency + human-review path. |
