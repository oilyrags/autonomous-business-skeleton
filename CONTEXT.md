# Autonomous AI-First Business Skeleton

The reusable operating system of an AI-run business: bounded contexts, accountable AI agents, an event backbone, deterministic controls for money/identity/consent, and compliance-by-construction. This is the tight, opinionated shared-language glossary for day-to-day agent work; the full long-form glossary is `architecture/02_ubiquitous_glossary.md`.

## Platform & governance

**Bounded Context**:
An explicit boundary inside which one domain model and its language are consistent; owns its data, integrates only via API, event, or ACL.
_Avoid_: module, service, microservice (when you mean the domain boundary)

**Agent**:
An accountable, identity-bearing AI actor with a charter, tools, permissions, authority level, and audit hooks.
_Avoid_: bot, assistant, script

**Authority Level**:
The autonomy (0–5) a process or agent is granted, per the autonomy authority matrix.
_Avoid_: permission tier, access level

**Guardrail**:
A hard pre/post condition enforced outside the LLM (policy engine, validators) that an agent cannot override.
_Avoid_: rule, check, constraint (when you mean the enforced kind)

**Kill Switch**:
A control that revokes agent credentials and halts tool execution within an SLA; global, per-context, or per-agent.
_Avoid_: stop button, circuit breaker (a circuit breaker is the narrower auto-trip control)

**Decision Record**:
The immutable record of a material decision (problem, options, data, framework, expected value, risks, dissent, owner, review date).
_Avoid_: ADR (an ADR is an architecture decision specifically), note, log entry

**Maker-Checker**:
Separation where the entity that creates an action cannot approve it.
_Avoid_: four-eyes, dual control (dual control is the human kill-switch case)

## Customer & revenue

**Contact**:
A natural person we hold personal data about; the DSAR subject unit.
_Avoid_: user, person, lead (a Lead is pre-qualification)

**Account**:
An organization we sell to or serve (B2B).
_Avoid_: company, org, client

**Customer**:
An Account or Contact with at least one active or past paid relationship.
_Avoid_: client, buyer

**Opportunity**:
A qualified potential deal with a stage, value, and close date.
_Avoid_: deal (until won), prospect

**Consent**:
A lawful-basis record capturing a data subject's permission for a stated channel and purpose, with grant/revoke timestamps.
_Avoid_: opt-in, permission, subscription

**Subscription**:
A recurring entitlement a Customer holds, driving billing and access.
_Avoid_: plan, licence (a plan is the catalog template)

## Finance

**Ledger Entry**:
An append-only, double-entry accounting record; immutable.
_Avoid_: transaction, posting, journal (informally)

**Invoice**:
A demand for payment issued to a Customer; an account receivable.
_Avoid_: bill, statement

**Revenue Recognition**:
Deterministic allocation of revenue to periods per policy (e.g. ratable for subscriptions).
_Avoid_: revrec (in prose), booking

**Spend Cap**:
A pre-authorized maximum an agent may commit without human approval.
_Avoid_: budget, limit (a Budget is the planned-spend aggregate)

## Data & AI

**Data Product**:
An owned, contracted, discoverable dataset with SLA, lineage, classification, and quality tests.
_Avoid_: dataset, table (when you mean the governed product)

**Metric**:
The single canonical definition of a KPI (one definition per KPI, in the semantic layer).
_Avoid_: measure, number, stat

**Model Gateway**:
The single ingress all model access routes through; maps a task profile to a model + deterministic fallback.
_Avoid_: LLM client, proxy, router (informally)

**Grounding**:
Constraining generation to retrieved, provenance-bearing sources; abstain when unsupported.
_Avoid_: RAG (RAG is the technique), citation (a citation is the artifact)

## Compliance & rights

**Data Subject Request (DSAR)**:
A request to exercise a right: access, erasure, portability, rectification, objection, or restriction.
_Avoid_: data request, GDPR request, deletion request (too narrow)

**Lawful Basis**:
The GDPR Art.6 ground for processing personal data (consent, contract, legitimate_interest, legal_obligation, vital_interest, public_task).
_Avoid_: justification, reason, legal ground

**Legal Hold**:
A suspension of erasure/retention for litigation or regulatory reasons; overrides deletion.
_Avoid_: freeze, retention lock

**Significant Automated Decision**:
An automated decision with legal or similarly significant effect on a person (GDPR Art.22); needs transparency + a human-review path.
_Avoid_: auto-decision, AI decision (too broad)
