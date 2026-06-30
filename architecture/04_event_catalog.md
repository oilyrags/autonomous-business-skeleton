# 04 — Event Catalog

The event backbone is the only async integration path between contexts. Every event below has: producer, consumers, payload schema reference, subject reference, data classification, retention policy, audit requirement, failure handling. Schemas are defined in `events.asyncapi.yaml`; this file is the human-readable index plus governance rules.

## Conventions

- **Envelope (all events):** `eventName`, `eventId` (uuid), `occurredAt` (ISO-8601), `producer`, `traceId`, `schemaVersion`, `dataClassification`, `subjectRef {type,id}`, then `payload`.
- **Topic naming:** `<context>.<aggregate>.<event>` (e.g. `finance.invoice.issued`).
- **Classifications:** `public | internal | confidential | personal | financial`. (`personal` and `financial` carry the strictest controls.)
- **Failure handling default:** at-least-once delivery, consumer idempotency by `eventId`, retry with exponential backoff → dead-letter-queue (DLQ) + alert. Per-event overrides noted.
- **Retention policy IDs** reference `08_data_inventory_template.json` retention rules.
- **Personal-data events** additionally declare lawful basis + DSAR impact.
- **Financial events** declare ledger impact or explicitly state none.

## Catalog

| Event | Producer | Key consumers | Class | Retention | Audit | Personal/DSAR | Ledger impact |
|---|---|---|---|---|---|---|---|
| `LeadCaptured` | crm.marketing | sales, data | personal | contact_retention | yes | basis: consent/legit_interest; DSAR: access+erasure | none |
| `ConsentGranted` | crm.marketing | sales, cs, compliance, data | personal | consent_retention (audit-long) | yes | basis: consent; DSAR: access+portability | none |
| `ConsentRevoked` | crm.marketing | sales, cs, compliance, data, ai_platform | personal | consent_retention | yes | basis: consent; DSAR: triggers suppression | none |
| `SegmentEntered` | crm.marketing | data, growth | personal | derived_short | yes | basis: legit_interest; DSAR: access | none |
| `CampaignLaunched` | crm.marketing | data, growth, executive | internal | ops_standard | yes | n/a | none |
| `MessageSuppressed` | crm.marketing | data, compliance | personal | consent_retention | yes | basis: legal_obligation; DSAR: access | none |
| `OpportunityQualified` | sales | finance, cs, data, executive | confidential | ops_standard | yes | n/a (account-level) | none |
| `QuoteIssued` | sales | finance, data | confidential | contract_retention | yes | n/a | none |
| `QuoteApproved` | sales (deal desk) | finance, data | confidential | contract_retention | yes | n/a | none |
| `DealWon` | sales | finance, cs, crm, data, executive | confidential | contract_retention | yes | n/a | none (triggers invoice) |
| `DealLost` | sales | growth, data, executive | confidential | ops_standard | yes | n/a | none |
| `ContractSigned` | sales/legal | finance, cs, compliance, data | confidential | contract_retention (legal-long) | yes | n/a | none |
| `InvoiceIssued` | finance.billing | crm, cs, data, executive | financial | financial_retention | yes | account contact (personal): access | **AR debit / revenue-deferred** |
| `PaymentReceived` | finance.billing | cs, data, executive | financial | financial_retention | yes | n/a | **cash debit / AR credit** |
| `PaymentFailed` | finance.billing | cs, sales, workflow, data | financial | financial_retention | yes | n/a | none (dunning trigger) |
| `RevenueRecognized` | finance.accounting | data, executive | financial | financial_retention | yes | n/a | **deferred→recognized revenue** |
| `LedgerEntryPosted` | finance.accounting | data, security(audit) | financial | financial_retention (immutable) | yes | n/a | **the ledger change itself** |
| `BudgetThresholdExceeded` | finance.fpna | executive, security, vendor | financial | ops_standard | yes | n/a | none |
| `ForecastUpdated` | finance.fpna | executive, data | financial | ops_standard | yes | n/a | none |
| `AnomalyDetected` | finance.fraud | security, compliance, executive | financial | ops_standard | yes | n/a | none |
| `TicketCreated` | customer_service | data, knowledge | personal | support_retention | yes | basis: contract; DSAR: access+erasure | none |
| `TicketEscalated` | customer_service | compliance(if rights), executive, people | personal | support_retention | yes | basis: contract; DSAR: access | none |
| `TicketResolved` | customer_service | crm, knowledge, data | personal | support_retention | yes | basis: contract; DSAR: access | none |
| `RefundProposed` | customer_service | finance, workflow | financial | financial_retention | yes | n/a | none (until approved) |
| `ChurnRiskDetected` | customer_service | crm, sales, executive | confidential | ops_standard | yes | account-level | none |
| `FeatureRequested` | product / cs | product, growth | internal | ops_standard | yes | n/a | none |
| `OpportunityScored` | product | executive, growth | internal | ops_standard | yes | n/a | none |
| `SpecApproved` | product | qa, data | internal | ops_long | yes | n/a | none |
| `BuildSucceeded` | product (ci) | qa | internal | ops_short | yes | n/a | none |
| `BuildFailed` | product (ci) | product, qa | internal | ops_short | yes | n/a | none |
| `ReleasePromoted` | product | qa, cs, data | internal | ops_long | yes | n/a | none |
| `DeploymentCompleted` | product | qa, executive | internal | ops_long | yes | n/a | none |
| `FeatureShipped` | product | crm, cs, knowledge, growth | internal | ops_standard | yes | n/a | none |
| `IncidentDetected` | qa.reliability | executive, cs, security, compliance | confidential | incident_retention | yes | n/a (assess if breach) | none |
| `IncidentResolved` | qa.reliability | executive, cs | confidential | incident_retention | yes | n/a | none |
| `ErrorBudgetExceeded` | qa.reliability | product, executive | internal | ops_standard | yes | n/a | none |
| `ExperimentStarted` | growth | data, product | internal | ops_standard | yes | n/a | none |
| `ExperimentConcluded` | growth | product, crm, executive, data | internal | ops_long | yes | n/a | none |
| `GuardrailBreached` | growth | product, executive | internal | ops_standard | yes | n/a | none |
| `DataSubjectRequestReceived` | compliance | all personal-data contexts, workflow | personal | dsar_retention | yes | basis: legal_obligation; **the DSAR itself** | none |
| `DataExportCompleted` | compliance | requesting subject channel, data | personal | dsar_retention | yes | DSAR: portability fulfilled | none |
| `DataDeletionCompleted` | compliance | all personal-data contexts, data | personal | dsar_retention (proof kept) | yes | DSAR: erasure fulfilled | none |
| `RectificationCompleted` | compliance | all personal-data contexts | personal | dsar_retention | yes | DSAR: rectification | none |
| `ObjectionRecorded` | compliance | crm, sales, data | personal | dsar_retention | yes | DSAR: objection | none |
| `RestrictionApplied` | compliance | all personal-data contexts | personal | dsar_retention | yes | DSAR: restriction | none |
| `DPIARequired` | compliance | executive, product | confidential | compliance_retention | yes | n/a | none |
| `BreachDeclared` | compliance | executive, security, all | confidential | compliance_retention | yes | may notify subjects | none |
| `ComplianceGateBlocked` | compliance | product, executive | internal | compliance_retention | yes | n/a | none |
| `PolicyViolationDetected` | security | compliance, executive, ai_platform | confidential | security_retention | yes | n/a | none |
| `PrincipalRegistered` | security | ai_platform, people | confidential | security_retention | yes | n/a | none |
| `PrincipalRevoked` | security | ai_platform, workflow, all | confidential | security_retention | yes | n/a | none |
| `CircuitBreakerTripped` | security | executive, ai_platform | confidential | security_retention | yes | n/a | none |
| `KillSwitchActivated` | security | **all** (halts agent action) | confidential | security_retention | yes | n/a | none |
| `ThreatDetected` | security | executive, compliance | confidential | security_retention | yes | n/a | none |
| `RateLimitExceeded` | security | ai_platform, executive | internal | ops_short | yes | n/a | none |
| `AgentDecisionMade` | any agent → executive | executive, security, compliance, data | confidential | decision_retention | yes | screen for Art.22 | none |
| `ApprovalRequired` | workflow | people (on-duty human), executive | confidential | decision_retention | yes | n/a | none |
| `ApprovalGranted` | workflow | requesting context, security | confidential | decision_retention | yes | n/a | none |
| `ApprovalDenied` | workflow | requesting context, executive | confidential | decision_retention | yes | n/a | none |
| `WorkflowStarted` / `WorkflowCompleted` / `WorkflowFailed` | workflow | requesting context, data | internal | ops_standard | yes | n/a | none |
| `SagaCompensated` | workflow | requesting context, executive | confidential | ops_long | yes | n/a | depends on saga |
| `ModelRegistered` / `ModelPromoted` | ai_platform | executive, security | internal | ops_long | yes | n/a | none |
| `ModelEvaluationFailed` | ai_platform | product, executive, security | confidential | ops_long | yes | n/a | none |
| `ToolRegistered` | ai_platform | security | confidential | ops_long | yes | n/a | none |
| `GuardrailTriggered` | ai_platform | security, compliance | confidential | security_retention | yes | n/a | none |
| `FallbackInvoked` | ai_platform | executive, data | internal | ops_short | yes | n/a | none |
| `VendorOnboarded` / `VendorOffboarded` | vendor | security, compliance, finance | confidential | contract_retention | yes | n/a | none |
| `VendorContractSigned` / `ContractRenewal` | vendor | finance, executive | confidential | contract_retention | yes | n/a | none |
| `WorkerOnboarded` / `WorkerOffboarded` | people | security, finance | personal | hr_retention | yes | basis: contract/employment; DSAR: access | none |
| `AccessGranted` / `AccessRevoked` | people / security | security | confidential | security_retention | yes | n/a | none |
| `ArtifactApproved` / `ArtifactDeprecated` | knowledge | cs, ai_platform, data | internal | ops_standard | yes | n/a | none |
| `DataProductRegistered` / `MetricDefined` | data | executive, all consumers | internal | ops_long | yes | n/a | none |
| `QualityCheckFailed` / `FreshnessSLABreached` | data | producing context, executive | internal | ops_standard | yes | n/a | none |

## Governance rules

1. **No event without a registered schema** in `events.asyncapi.yaml` (CI-enforced).
2. **No personal-data event** ships without lawful basis + DSAR impact declared (Compliance gate).
3. **Financial events** must state ledger impact; ledger-changing events are emitted only by Finance after a deterministic, balanced posting.
4. **`KillSwitchActivated`** is a priority broadcast; all agent runtimes must stop initiating tool calls on receipt within the kill-switch SLA.
5. **DSAR events** (`DataSubjectRequestReceived`, `*Completed`) fan out to every personal-data context and are tracked to completion by the Workflow saga (`16` compliance verification).
6. **DLQ + alert** on repeated consumer failure; poison messages quarantined, never silently dropped.
