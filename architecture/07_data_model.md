# 07 — Canonical Business Data Model

The canonical model defines shared entity *meaning* (ubiquitous language) but **not** shared storage. Each entity has exactly one owning bounded context that is its system of record; other contexts hold references or ACL-translated projections. `priv` = privacy classification; `ret` = retention policy id (see `08`); `audit` = audit-required.

## Entity reference

| Entity | Owning context | Purpose | Key attributes | Key relationships | priv | ret | audit |
|---|---|---|---|---|---|---|---|
| **Organization** | Security/Platform | The operating company / tenant root | id, legalName, jurisdiction, residency | has Users, Agents, Policies | internal | ops_long | yes |
| **User** | People & Workforce | A human principal | id, role, email, accessGrants | belongs Organization; has Roles | personal | hr_retention | yes |
| **Agent** | AI Platform / Security | An AI principal | agentId, charter, authorityLevel, modelBinding | has Role, Tools; emits Decisions | confidential | ops_long | yes |
| **Role** | Security | Permission bundle | id, name, permissions[] | granted to User/Agent | confidential | security_retention | yes |
| **Policy** | Security/Compliance | Policy-as-code rule | id, type, ruleRef, version | governs Commands/Events | confidential | compliance_retention | yes |
| **Customer** | Sales/CRM (shared id) | Paying/served relationship | id, type(B2B/B2C), status | links Account/Contact, Subscription | personal | contact_retention | yes |
| **Account** | Sales | Organization we serve (B2B) | id, name, segment, owner | has Contacts, Opportunities | confidential | contract_retention | yes |
| **Contact** | CRM & Marketing | A natural person (DSAR unit) | id, name, email, consentState | belongs Account; has Consent | **personal** | contact_retention | yes |
| **Lead** | CRM & Marketing | Unqualified interest | id, source, score, lawfulBasis | converts to Contact/Opportunity | personal | contact_retention | yes |
| **Opportunity** | Sales | Qualified potential deal | id, stage, value, closeDate | belongs Account; yields Quote | confidential | contract_retention | yes |
| **Campaign** | CRM & Marketing | Marketing initiative | id, channels, audience, content | targets Segment | internal | ops_standard | yes |
| **Segment** | CRM & Marketing | Targeting cohort | id, definition, version | contains Contacts (derived) | personal | derived_short | yes |
| **Consent** | CRM & Marketing | Lawful-basis record | id, purpose, channel, grant/revokeAt | belongs Contact | **personal** | consent_retention | yes |
| **Product** | Product Engineering | Sellable offering | id, name, skus, lifecycle | has Features, Subscriptions | public/internal | ops_long | yes |
| **Feature** | Product Engineering | Shippable capability | id, flag, status | belongs Product; in Release | internal | ops_long | yes |
| **Experiment** | Experimentation & Growth | Controlled test | id, hypothesis, variants, metrics | affects Feature/Campaign | internal | ops_long | yes |
| **Release** | Product Engineering | Reversible deployment | id, version, rolloutPlan | contains Features | internal | ops_long | yes |
| **Incident** | QA & Reliability | Degradation/outage | id, severity, status, postmortem | affects Release/Product | confidential | incident_retention | yes |
| **Subscription** | Finance/Sales | Recurring entitlement | id, plan, term, status | belongs Customer; drives Invoice | financial | financial_retention | yes |
| **Contract** | Sales/Legal | Binding agreement | id, terms, signedAt, value | belongs Account | confidential | contract_retention (legal) | yes |
| **Invoice** | Finance | Demand for payment (AR) | id, amount, dueDate, status | belongs Account; has Payments | **financial** | financial_retention | yes |
| **Payment** | Finance | Money movement | id, amount, method, status | settles Invoice | **financial** | financial_retention | yes |
| **Expense** | Finance | Outgoing cost | id, amount, category, vendor | links Vendor; posts Ledger | financial | financial_retention | yes |
| **LedgerEntry** | Finance | Double-entry record | id, debit, credit, account, ts | immutable; source of truth | **financial** | financial_retention (immutable) | yes |
| **Budget** | Finance | Planned spend | id, period, allocations | constrains Expense/Campaign | financial | ops_long | yes |
| **Forecast** | Finance | Projected financials | id, scenario, horizon, values | derived from Ledger+Sales | financial | ops_standard | yes |
| **Ticket** | Customer Service | Support request | id, status, sla, conversation | belongs Customer | **personal** | support_retention | yes |
| **Conversation** | Customer Service | Message thread | id, channel, messages[] | belongs Ticket | **personal** | support_retention | yes |
| **KnowledgeArtifact** | Knowledge Mgmt | Grounding source | id, content, provenance, approval | indexed for retrieval | internal | ops_standard | yes |
| **DataSubjectRequest** | Compliance | Rights request | id, right, subjectId, dueBy, status | spans all personal-data ctx | **personal** | dsar_retention | yes |
| **AuditEvent** | Security | Immutable action record | id, principal, action, ts, traceId | references any entity | confidential | security_retention (immutable) | yes |
| **Risk** | Security/Compliance | Tracked risk item | id, category, severity, owner | mitigated by Control | confidential | compliance_retention | yes |
| **Control** | Security/Compliance | Mitigating mechanism | id, type, status, evidenceRef | mitigates Risk | confidential | compliance_retention | yes |
| **Model** | AI Platform | LLM/ML artifact | id, version, taskProfiles, card | bound to Agents | internal | ops_long | yes |
| **ModelEvaluation** | AI Platform | Eval scoring | id, evalSet, scores, passed | tests Model | internal | ops_long | yes |
| **Decision** | Executive | Material decision record | id, framework, EV, owner, status | references Data, Agents | confidential | decision_retention | yes |
| **Task** | Workflow | Unit of work | id, type, assignee, status | within Workflow | internal | ops_standard | yes |
| **Workflow** | Workflow | Durable process instance | id, definition, state, history | orchestrates Tasks/Approvals | internal | ops_long | yes |
| **Metric** | Data Platform | Canonical KPI definition | name, definition, version, owner | one per KPI | internal | ops_long | yes |
| **DataProduct** | Data Platform | Contracted dataset | id, contract, sla, lineage, class | consumed cross-context | varies | ops_long | yes |
| **Vendor** | Vendor & Procurement | Third party | id, riskTier, dpa, subprocessors | has Contract; processes data | confidential | contract_retention | yes |

## Modeling rules

1. **One system of record per entity.** Shared identifiers (e.g. `Customer.id`) are coordinated, but each context stores only its owned attributes; foreign attributes arrive via API/event projection through an ACL.
2. **Personal-data entities** (Contact, Consent, Lead, Ticket, Conversation, User, DataSubjectRequest, plus personal fields on Invoice/Account) all map into `08` and implement the Subject Rights API.
3. **Financial entities** (LedgerEntry, Invoice, Payment, Expense) are append-only or maker-checker-corrected; never silently mutated.
4. **AuditEvent and LedgerEntry are immutable** — corrections are new entries, not edits.
5. **Decision** links the evidence (Data/Metric), the framework, and the approval chain — it is the join between the Decision OS (`13`) and everything else.
6. **Aggregate boundaries** (from `03`) define transaction scope; cross-aggregate consistency is eventual, via events.

## Relationship overview (text ER)

```
Organization 1─* User ; 1─* Agent ; 1─* Policy
Account 1─* Contact ; 1─* Opportunity ; 1─1 Customer(B2B)
Contact 1─* Consent ; 1─* Ticket ; 1─* Lead(origin)
Opportunity 1─* Quote ; 1─1 Contract(on win)
Contract 1─* Subscription ; Subscription 1─* Invoice ; Invoice 1─* Payment
Invoice *─1 Account ; Payment ─posts→ LedgerEntry ; Expense ─posts→ LedgerEntry ; Expense *─1 Vendor
Decision *─* Metric (dataUsed) ; Decision *─1 Agent(owner) ; Decision ─emits→ AuditEvent
Workflow 1─* Task ; Workflow 1─* ApprovalRequest ; DataSubjectRequest ─spans→ (all personal-data contexts)
Model 1─* ModelEvaluation ; Agent *─1 Model(binding) ; Risk *─* Control
```
