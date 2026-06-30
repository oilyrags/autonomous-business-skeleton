# 03 — Domain Catalog

Sixteen bounded contexts. Each meets the structural minimum (≥3 aggregates, ≥5 commands, ≥5 events, ≥3 policies/invariants) and declares owned data, APIs, subscribed/emitted events, ACLs, agent roster, human approval points, compliance, observability, failure modes, KPIs. Event payloads/schemas live in `04` + `events.asyncapi.yaml`; agents in `05`; authority in `06`.

Notation: **Cmd** = command, **Evt** = emitted event, **Sub** = subscribed event, **Agg** = aggregate, **VO** = value object, **Inv** = invariant/policy.

---

## 1. Executive Strategy & Decision Intelligence

- **Purpose:** Set strategy, allocate capital across the venture portfolio, own the Decision Operating System, and run the agentic C-suite cadences.
- **Ubiquitous language:** OKR, Horizon (1/2/3), Portfolio, Capital Allocation, Decision Record, Expected Value, Dissent.
- **Subdomains:** strategy formulation (core), portfolio management (core), capital allocation (core), decision intelligence (supporting), board reporting (supporting).
- **Aggregates:** `Strategy` (objectives, horizons), `PortfolioVenture` (idea→scale lifecycle), `Decision` (decision record + approval chain).
- **Entities/VOs:** Objective, KeyResult, CapitalAllocation, ExpectedValue(VO), RiskProfile(VO), Dissent(VO).
- **Commands:** `SetObjective`, `AllocateCapital`, `OpenDecision`, `RecordDissent`, `ApproveDecision`, `KillVenture`.
- **Domain events (Evt):** `ObjectiveSet`, `CapitalAllocated`, `DecisionMade` (`AgentDecisionMade`), `ApprovalRequired`, `VentureGateChanged`, `PortfolioReviewed`.
- **Subscribed (Sub):** `ForecastUpdated`, `BudgetThresholdExceeded`, `ExperimentConcluded`, `IncidentDetected`, `PolicyViolationDetected`, semantic metrics (via Data ACL).
- **Policies/invariants:** (1) No capital allocation without a Decision Record citing data + framework. (2) Safety/compliance/ethics are hard constraints, never traded off. (3) Every material decision has a review date and outcome-review. (4) Dissent from any C-agent must be recorded, never suppressed.
- **Data ownership:** strategy docs, OKRs, decision registry, portfolio state. Reads metrics only via Data semantic layer (ACL).
- **APIs:** `POST /decisions`, `GET /decisions/{id}`, `POST /capital-allocations`, `GET /portfolio`, `GET /okrs`.
- **Agent roster:** CEO, COO, CFO, CTO, CPO, CMO, CRO, CCO, CDO, CISO, CLO, CHRO (see `11`/`05`).
- **Human approval points:** capital allocation above threshold; venture kill; strategy pivots; anything Art.22-significant.
- **Compliance:** decisions affecting persons routed through Compliance; no personal data processed here beyond aggregates.
- **Observability:** decision latency, % decisions with complete provenance, forecast-vs-actual.
- **Failure modes:** stale metrics → decisions on bad data (mitigation: freshness SLA gate); groupthink (mitigation: mandatory independent dissent agent).
- **KPIs:** OKR attainment, capital efficiency (ROIC), decision quality (outcome-review pass rate), portfolio NPV.

---

## 2. Product Engineering

- **Purpose:** The autonomous software factory — discover, design, build, and document product.
- **Ubiquitous language:** JTBD, Opportunity, Spec, ADR, PR, Feature Flag, SLO, Error Budget.
- **Subdomains:** discovery (core), delivery/CI-CD (core), architecture governance (supporting), docs generation (generic).
- **Aggregates:** `Opportunity` (JTBD + score), `Spec` (requirements + ADRs), `Release` (build→deploy→rollback).
- **Entities/VOs:** Requirement, ADR, PullRequest, FeatureFlag, BuildArtifact, SLO(VO), RolloutPlan(VO).
- **Commands:** `ScoreOpportunity`, `ApproveSpec`, `GenerateCode`, `OpenPullRequest`, `PromoteRelease`, `RollbackRelease`.
- **Evt:** `OpportunityScored`, `SpecApproved`, `BuildSucceeded`, `BuildFailed`, `ReleasePromoted`, `DeploymentCompleted`, `FeatureShipped`.
- **Sub:** `FeatureRequested`, `ExperimentConcluded`, `IncidentDetected`, `ObjectiveSet`.
- **Policies/invariants:** (1) No green tests → no ship. (2) No secrets in code (scan-gated). (3) Every release reversible (rollback path required). (4) PII never logged in plaintext. (5) Spec approval required before code-gen for changes above complexity threshold.
- **Data ownership:** repos, specs, ADRs, build/deploy metadata, feature-flag state.
- **APIs:** `POST /opportunities`, `POST /specs`, `POST /releases/{id}/promote`, `POST /releases/{id}/rollback`, `GET /flags`.
- **Agent roster:** Product Discovery Agent, Spec Agent, Code-Gen Agent, Code-Review Agent, Release Agent (see QA for test agents).
- **Human approval points:** production promotion of high-risk releases; ADRs with cross-context impact; schema/contract-breaking changes.
- **Compliance:** privacy-by-design checklist on specs touching personal data; accessibility gate.
- **Observability:** DORA (deploy freq, lead time, CFR, MTTR), build success rate, flag debt.
- **Failure modes:** hallucinated code (mitigation: tests + review gate); flag sprawl; rollback failure (mitigation: rollback drill in CI).
- **KPIs:** DORA four, escaped defects, change failure rate, SLO attainment.

---

## 3. QA, Reliability & Release Management

- **Purpose:** Guarantee quality, reliability, and safe release; own SLOs, error budgets, and incident management.
- **Ubiquitous language:** Test Suite, Coverage, Contract Test, Error Budget, Incident, MTTR, Progressive Delivery.
- **Subdomains:** test generation/execution (core), release safety (core), incident management (core), reliability/SLO (supporting).
- **Aggregates:** `TestRun` (suite + results), `Incident` (detect→resolve→postmortem), `ErrorBudget` (per service/SLO).
- **Entities/VOs:** TestCase, CoverageReport, SLOTarget(VO), Postmortem, RollbackDecision(VO).
- **Commands:** `GenerateTests`, `RunSuite`, `GateRelease`, `OpenIncident`, `ResolveIncident`, `BurnErrorBudget`.
- **Evt:** `TestsGenerated`, `SuitePassed`, `SuiteFailed`, `ReleaseGated`, `IncidentDetected`, `IncidentResolved`, `ErrorBudgetExceeded`.
- **Sub:** `BuildSucceeded`, `ReleasePromoted`, `DeploymentCompleted`.
- **Policies/invariants:** (1) Release blocked unless unit+integration+contract+security suites green. (2) SLO breach freezes non-critical deploys (error-budget policy). (3) Every Sev1/Sev2 incident requires a blameless postmortem. (4) Accessibility + performance suites mandatory before GA.
- **Data ownership:** test results, coverage, SLO/error-budget state, incident records, postmortems.
- **APIs:** `POST /test-runs`, `GET /test-runs/{id}`, `POST /release-gates`, `POST /incidents`, `GET /slos`.
- **Agent roster:** Test-Gen Agent, Reliability Agent, Incident-Commander Agent.
- **Human approval points:** waiving a failed gate (requires named approver + justification); Sev1 external comms.
- **Compliance:** incident records feed breach-assessment to Compliance when personal data involved.
- **Observability:** MTTR, change failure rate, escaped defects, SLO attainment, flaky-test rate.
- **Failure modes:** flaky tests erode trust (mitigation: quarantine + flake budget); alert fatigue; gate bypass (mitigation: gate-waiver audit event).
- **KPIs:** MTTR, CFR, SLO attainment, escaped defects, postmortem action closure rate.

---

## 4. CRM & Marketing

- **Purpose:** The lawful growth engine — acquire, segment, and nurture demand with consent.
- **Ubiquitous language:** ICP, STP, Consent, Suppression List, Campaign, Lifecycle Journey, Attribution, Deliverability.
- **Subdomains:** consent/preference (core, compliance-critical), campaign ops (core), lifecycle/journeys (core), attribution/MMM (supporting), content ops (supporting).
- **Aggregates:** `Contact` (person + consent state), `Segment` (cohort definition + membership), `Campaign` (channels, audience, content).
- **Entities/VOs:** Consent(VO with purpose+channel+timestamp), Preference, JourneyStep, ContentAsset, AttributionModel(VO).
- **Commands:** `CaptureLead`, `GrantConsent`, `RevokeConsent`, `LaunchCampaign`, `EnterJourney`, `SuppressContact`.
- **Evt:** `LeadCaptured`, `ConsentGranted`, `ConsentRevoked`, `SegmentEntered`, `CampaignLaunched`, `MessageSuppressed`.
- **Sub:** `InvoiceIssued`, `DealWon`, `ExperimentConcluded`, `TicketResolved`, `DataDeletionCompleted`.
- **Policies/invariants:** (1) No outreach without a valid lawful basis for that channel+purpose. (2) Consent revocation + suppression enforced before next send (synchronous check). (3) No dark patterns; opt-out as easy as opt-in. (4) Generated claims truthful, grounded, brand-safe (claim-check gate). (5) Special-category data never used for targeting unless a pack permits.
- **Data ownership:** contacts, consent records, segments, campaigns, content, attribution models. (Consent is the system of record; other contexts read via API/ACL.)
- **APIs:** `POST /leads`, `POST /consents`, `DELETE /consents/{id}`, `GET /contacts/{id}/consent`, `POST /campaigns`, `GET /suppression`.
- **Agent roster:** ICP/Segmentation Agent, Campaign Agent, Content Agent, Deliverability Agent, Attribution Agent.
- **Human approval points:** brand-risk content; paid-spend above cap; new lawful-basis category; large-audience sends.
- **Compliance:** consent system of record; implements SubjectRights API (access/erasure/objection); ePrivacy/cookie rules.
- **Observability:** consent coverage %, suppression-respect rate, deliverability/bounce, CAC by channel.
- **Failure modes:** sending to suppressed contact (mitigation: hard pre-send guardrail + audit); hallucinated claims (claim-check); deliverability blacklisting.
- **KPIs:** AARRR funnel, LTV:CAC, payback period, cohort retention, deliverability rate, consent coverage.

---

## 5. Sales & Revenue Operations

- **Purpose:** Convert qualified demand to revenue within approved pricing and legal policy.
- **Ubiquitous language:** Opportunity, MEDDIC/BANT, Pipeline Stage, CPQ, Quote, Deal Desk, Discount Threshold.
- **Subdomains:** lead routing/qualification (core), CPQ/quoting (core, money-adjacent), forecasting (supporting), renewal/expansion (core), win/loss (supporting).
- **Aggregates:** `Opportunity` (stage, value, qualification), `Quote` (line items, discount, validity), `RenewalCase`.
- **Entities/VOs:** QualificationScore(VO), PriceBook, DiscountPolicy(VO), Proposal, ForecastCommit(VO).
- **Commands:** `RouteLead`, `QualifyOpportunity`, `CreateQuote`, `ApproveQuote`, `MarkWon`, `MarkLost`, `OpenRenewal`.
- **Evt:** `OpportunityQualified`, `QuoteIssued`, `QuoteApproved`, `DealWon`, `DealLost`, `RenewalOpened`, `ForecastUpdated`.
- **Sub:** `LeadCaptured`, `ConsentGranted`, `InvoiceIssued`, `PaymentReceived`, `EntitlementChanged`.
- **Policies/invariants:** (1) No binding price/legal commitment outside approved policy. (2) Quote creation segregated from quote approval (maker-checker). (3) Discounts above threshold require approval. (4) Every commitment logged immutably. (5) Forecast must reconcile to pipeline coverage rules.
- **Data ownership:** opportunities, quotes, price books, forecasts, win/loss notes.
- **APIs:** `POST /opportunities/{id}/qualify`, `POST /quotes`, `POST /quotes/{id}/approve`, `POST /opportunities/{id}/won`, `GET /forecast`.
- **Agent roster:** Lead-Routing Agent, SDR/Qualification Agent, Conversational-Sales Agent, CPQ Agent, Deal-Desk Agent, Forecast Agent.
- **Human approval points:** non-standard contract terms; discount > threshold; custom pricing; multi-year commitments.
- **Compliance:** ACL on inbound Marketing consent; contract terms routed to Legal; implements SubjectRights API.
- **Observability:** pipeline coverage, win rate, quote cycle time, discount distribution, forecast accuracy.
- **Failure modes:** over-discounting (cap + approval); fabricated commitments (policy gate); forecast bias (deterministic coverage model).
- **KPIs:** win rate, ACV, pipeline coverage, forecast accuracy, discount leakage, expansion/NRR.

---

## 6. Finance, Accounting, Billing & FP&A

- **Purpose:** The autonomous financial control system — ledger, billing, AR/AP, close, treasury, forecasting.
- **Ubiquitous language:** Chart of Accounts, Double-Entry, Ledger Entry, Invoice, Revenue Recognition, Reconciliation, Maker-Checker, Spend Cap.
- **Subdomains:** ledger/accounting (core, deterministic), billing/AR (core), AP/expense (core), FP&A/forecasting (core), treasury (core), fraud/anomaly (supporting).
- **Aggregates:** `LedgerAccount` (append-only entries), `Invoice` (AR lifecycle), `Payment`, `Budget`/`Forecast`.
- **Entities/VOs:** JournalEntry, RevenueSchedule(VO), PaymentInstruction, SpendCap(VO), ReconciliationResult(VO).
- **Commands:** `PostJournalEntry`, `IssueInvoice`, `RecordPayment`, `InitiatePayment`, `RecognizeRevenue`, `ApprovePayment`, `RunForecast`.
- **Evt:** `InvoiceIssued`, `PaymentReceived`, `PaymentFailed`, `RevenueRecognized`, `LedgerEntryPosted`, `BudgetThresholdExceeded`, `ForecastUpdated`, `AnomalyDetected`.
- **Sub:** `DealWon`, `ContractSigned`, `SubscriptionChanged`, `VendorInvoiceReceived`, `RefundRequested`.
- **Policies/invariants:** (1) Ledger is append-only and balanced (debits=credits). (2) All financial math deterministic + verifiable (no LLM arithmetic). (3) No money moves beyond capped, pre-authorized, rules-based payments. (4) Maker-checker + separation-of-duties on payments, refunds, credits, discounts above threshold, budget changes, revrec. (5) Revenue recognized per documented policy only.
- **Data ownership:** ledger, invoices, payments, budgets, forecasts, tax records. **Most sensitive financial store.**
- **APIs:** `POST /journal-entries`, `POST /invoices`, `POST /payments`, `POST /payments/{id}/approve`, `GET /forecast`, `GET /statements`.
- **Agent roster:** FP&A Agent, Billing Agent, AR/Collections Agent, AP Agent, Treasury Agent, Anomaly-Detection Agent. (CFO Agent in Executive.)
- **Human approval points:** any payment above cap; new payee; budget reallocation; revrec policy change; cash transfers; tax filings.
- **Compliance:** financial-records retention (legal_obligation basis); SOX-lite controls (finance pack); implements SubjectRights API with **erasure-blocked-by-legal-hold** for financial records.
- **Observability:** ledger balance integrity check, close cycle time, DSO, forecast accuracy, payment-failure rate, anomaly count.
- **Failure modes:** double-payment (idempotency keys + maker-checker); revrec error (deterministic schedule engine); fraud (anomaly agent + cap).
- **KPIs:** three-statement accuracy, gross/contribution margin, runway, DSO/DPO, close time, forecast accuracy.

---

## 7. Customer Service & Customer Success

- **Purpose:** Resolve issues, retain and grow customers; grounded, entitlement-aware support.
- **Ubiquitous language:** Ticket, Triage, RAG-grounded Answer, Entitlement, SLA, Escalation, Health Score, Churn Risk.
- **Subdomains:** support/ticketing (core), grounded answering (core), success/health (core), VoC intelligence (supporting), refund/comp policy (supporting, money-adjacent).
- **Aggregates:** `Ticket` (conversation + resolution), `CustomerHealth` (score + signals), `KnowledgeAnswer` (grounded response).
- **Entities/VOs:** Conversation, Message, SLATarget(VO), Sentiment(VO), RefundProposal, EscalationReason(VO).
- **Commands:** `CreateTicket`, `TriageTicket`, `AnswerTicket`, `EscalateTicket`, `ResolveTicket`, `ProposeRefund`, `ScoreHealth`.
- **Evt:** `TicketCreated`, `TicketTriaged`, `TicketEscalated`, `TicketResolved`, `RefundProposed`, `ChurnRiskDetected`, `HealthScored`.
- **Sub:** `DealWon`, `InvoiceIssued`, `PaymentFailed`, `IncidentDetected`, `FeatureShipped`, `DataSubjectRequestReceived`.
- **Policies/invariants:** (1) Answers must be grounded in approved knowledge sources with provenance; if ungrounded/uncertain → escalate. (2) DSAR/privacy requests routed to Compliance workflow, never answered ad hoc. (3) Regulated advice, legal complaints, safety issues, vulnerable-customer signals, high-emotion cases escalate immediately. (4) Refunds/credits within policy + cap only; above → maker-checker via Finance. (5) Actions entitlement-checked.
- **Data ownership:** tickets, conversations, health scores, VoC themes, CS knowledge usage.
- **APIs:** `POST /tickets`, `POST /tickets/{id}/answer`, `POST /tickets/{id}/escalate`, `GET /customers/{id}/health`, `POST /refund-proposals`.
- **Agent roster:** Triage Agent, Support-Answer Agent (RAG), Escalation Agent, Customer-Success/Health Agent, VoC Agent.
- **Human approval points:** refunds/comp above cap; vulnerable-customer cases; legal/safety escalations; goodwill exceptions.
- **Compliance:** front door for many DSARs; vulnerable-customer handling; conversation-retention policy; implements SubjectRights API.
- **Observability:** CSAT, first-response/resolution time, SLA attainment, grounding rate, escalation rate, deflection.
- **Failure modes:** hallucinated answer (grounding gate + escalate-on-uncertainty); wrong entitlement action (entitlement check); missed vulnerability signal (classifier + audit).
- **KPIs:** CSAT/NPS, SLA attainment, resolution time, grounded-answer %, churn, NRR contribution.

---

## 8. Data Platform & Intelligence

- **Purpose:** The trusted data fabric — data products, semantic layer, vector/KG, lineage, quality, decision intelligence.
- **Ubiquitous language:** Data Product, Data Contract, Medallion (bronze/silver/gold), Semantic Metric, Feature Store, Lineage, Freshness SLA.
- **Subdomains:** ingestion/CDC (core), lakehouse/medallion (core), semantic/metrics (core), vector+KG (core), catalog/lineage/quality (core), decision intelligence (supporting).
- **Aggregates:** `DataProduct` (dataset + contract + SLA), `Metric` (canonical definition), `DataQualityCheck` (test suite + results).
- **Entities/VOs:** DataContract(VO), LineageEdge, FreshnessSLA(VO), Classification(VO), Embedding, KnowledgeGraphNode.
- **Commands:** `RegisterDataProduct`, `DefineMetric`, `IngestEvent`, `RunQualityChecks`, `PublishGoldTable`, `IndexForRetrieval`.
- **Evt:** `DataProductRegistered`, `MetricDefined`, `QualityCheckFailed`, `FreshnessSLABreached`, `DatasetPublished`, `LineageUpdated`.
- **Sub:** *all* domain events (event ingestion); `DataDeletionCompleted` (propagate erasure into lake).
- **Policies/invariants:** (1) Every KPI has exactly one canonical semantic definition. (2) Every dataset has owner, lineage, freshness SLA, classification, retention. (3) PII classified at ingestion. (4) Retrieved facts carry provenance or retrieval escalates. (5) No silent metric redefinition (versioned, reviewed).
- **Data ownership:** lakehouse, semantic layer, feature/vector stores, KG, catalog, lineage graph. (Stores *copies/derivations*; source-of-truth stays in owning contexts.)
- **APIs:** `POST /data-products`, `GET /metrics/{name}`, `POST /metrics`, `GET /lineage/{asset}`, `POST /retrieval/query`, `GET /quality/{product}`.
- **Agent roster:** Data-Product Agent, Semantic/Metrics Agent, Data-Quality Agent, Retrieval/Grounding Agent.
- **Human approval points:** new metric definition affecting board KPIs; reclassification of data sensitivity; cross-border dataset transfer.
- **Compliance:** classification engine; honors erasure propagation; lineage = evidence for RoPA; access policy enforcement.
- **Observability:** freshness SLA attainment, quality-check pass rate, lineage coverage, retrieval grounding rate.
- **Failure modes:** metric drift/duplication (single-definition guardrail); stale data feeding decisions (freshness gate); PII leak into gold (classification + masking).
- **KPIs:** % KPIs with one definition, data-product SLA attainment, quality pass rate, retrieval precision/grounding.

---

## 9. Compliance, Privacy & Legal

- **Purpose:** Compliance-by-construction — GDPR, DSAR, consent, RoPA, DPIA, AI transparency, contract review, breach response, evidence.
- **Ubiquitous language:** Lawful Basis, DSAR, RoPA, DPIA, Legal Hold, Significant Automated Decision, Evidence Store.
- **Subdomains:** subject rights (core), records/RoPA (core), DPIA/risk (core), AI transparency & human review (core), contract/legal review (supporting), breach response (core).
- **Aggregates:** `DataSubjectRequest` (intake→fulfilment→evidence), `ProcessingActivity` (RoPA entry), `DPIA`.
- **Entities/VOs:** LawfulBasis(VO), ConsentReference, RetentionRule(VO), LegalHold, BreachCase, TransparencyNotice.
- **Commands:** `ReceiveDSAR`, `FulfilAccess`, `FulfilErasure`, `FulfilPortability`, `OpenDPIA`, `PlaceLegalHold`, `OpenBreachCase`, `BlockRelease`.
- **Evt:** `DataSubjectRequestReceived`, `DataExportCompleted`, `DataDeletionCompleted`, `RectificationCompleted`, `ObjectionRecorded`, `RestrictionApplied`, `DPIARequired`, `BreachDeclared`, `ComplianceGateBlocked`.
- **Sub:** `ConsentRevoked`, `PolicyViolationDetected`, `AgentDecisionMade` (for Art.22 screening), `IncidentDetected`.
- **Policies/invariants:** (1) No personal data without lawful basis + inventory entry. (2) Erasure propagates per policy and is evidenced (unless legal hold). (3) Compliance gates block release. (4) DPIA required before high-risk processing goes live. (5) Significant automated decisions get a transparency notice + human-review path. (6) Never claim legal certainty — produce evidence + review.
- **Data ownership:** DSAR records, RoPA, DPIAs, legal holds, breach cases, evidence store, transparency notices.
- **APIs:** **Subject Rights API (mandatory, every personal-data context implements the consumer side)** — `POST /dsar`, `GET /dsar/{id}`, `POST /dsar/{id}/access`, `POST /dsar/{id}/erasure`, `POST /dsar/{id}/portability`, `POST /dsar/{id}/rectify`, `POST /dsar/{id}/object`, `POST /dsar/{id}/restrict`; plus `POST /dpia`, `POST /legal-holds`, `POST /breach-cases`.
- **Agent roster:** DSAR Orchestrator Agent, RoPA Agent, DPIA Agent, Contract-Review Agent, Breach-Response Agent. (CLO Agent in Executive.)
- **Human approval points:** DPIA sign-off; breach notification to regulator/subjects; contract execution; high-risk processing go-live; erasure-vs-legal-hold conflicts.
- **Compliance:** this *is* the compliance context; coordinates GDPR + active packs.
- **Observability:** DSAR SLA (e.g. ≤30 days), erasure-propagation completeness, DPIA coverage of high-risk, gate-block count, breach time-to-notify.
- **Failure modes:** incomplete erasure propagation (saga + completeness check across all contexts); missed DPIA trigger (automated trigger rules); fabricated legal claim (no-certainty policy).
- **KPIs:** DSAR on-time %, erasure completeness %, DPIA coverage, open legal-risk items, gate effectiveness.

---

## 10. Security, Risk & Trust

- **Purpose:** The safe-autonomy control plane — agent identity, least privilege, secrets, threat modeling, kill switch, prompt-injection/exfiltration defense.
- **Ubiquitous language:** Principal, Zero Trust, RBAC/ABAC, Secret, SBOM, Kill Switch, Circuit Breaker, Spend/Rate Limit.
- **Subdomains:** identity & access (core), secrets/keys (core), supply-chain security (core), threat detection/SIEM (core), safe-autonomy controls (core), BC/DR (supporting).
- **Aggregates:** `Principal` (human/agent identity + permissions), `PolicyDecision` (authZ result), `KillSwitchState`.
- **Entities/VOs:** Role, Permission(VO), Secret(ref), CircuitBreaker(VO), RateLimit(VO), SpendLimit(VO), ThreatEvent.
- **Commands:** `RegisterPrincipal`, `GrantRole`, `RevokePrincipal`, `EvaluatePolicy`, `TripCircuitBreaker`, `ActivateKillSwitch`, `IssueSecret`.
- **Evt:** `PrincipalRegistered`, `PrincipalRevoked`, `PolicyViolationDetected`, `CircuitBreakerTripped`, `KillSwitchActivated`, `ThreatDetected`, `RateLimitExceeded`.
- **Sub:** `AgentDecisionMade`, `BudgetThresholdExceeded`, `VendorOnboarded`, all tool-call audit events.
- **Policies/invariants:** (1) Every agent action authenticated, authorized, logged, explainable, revocable. (2) Least privilege default-deny. (3) Irreversible/high-impact/legally-binding/threshold-exceeding actions require approval. (4) A working kill switch is a launch blocker. (5) No secret in code/logs. (6) Every externally-triggered agent flow has prompt-injection + exfiltration controls.
- **Data ownership:** identity store, policies, audit log (system of record), secrets metadata, threat events, SBOMs.
- **APIs:** `POST /principals`, `POST /authz/evaluate`, `POST /principals/{id}/revoke`, `POST /kill-switch`, `GET /audit`, `POST /circuit-breakers`.
- **Agent roster:** Threat-Detection Agent, Access-Review Agent, Supply-Chain/SBOM Agent, Red-Team Agent. (CISO Agent in Executive.)
- **Human approval points:** kill-switch deactivation; new high-privilege role; production secret rotation policy; accepting a critical CVE risk.
- **Compliance:** audit log = evidence backbone for Compliance; access logging supports DSAR/security.
- **Observability:** authZ deny rate, time-to-revoke, kill-switch drill success, prompt-injection block rate, mean-time-to-detect.
- **Failure modes:** over-privileged agent (periodic access review + least-privilege default); prompt injection → tool abuse (input/output filtering, tool allow-list, human gate on sensitive tools); kill-switch failure (regular drills).
- **KPIs:** % actions authorized+logged, MTTD/MTTR (security), kill-switch RTO, critical-vuln age, exfiltration attempts blocked.

---

## 11. AI Model Operations & Agent Platform

- **Purpose:** Run the model gateway, tool registry, agent runtime, memory, evals, tracing — the substrate every agent uses.
- **Ubiquitous language:** Model Gateway, Task Profile, Tool Registry, Agent Runtime, Eval Set, Trace, Fallback Profile.
- **Subdomains:** model serving/gateway (core), tool registry/governance (core), agent runtime/memory (core), evals/quality (core), tracing/LLMOps (supporting).
- **Aggregates:** `Model` (version + binding), `ToolDefinition` (schema + permissions), `EvalRun` (set + scores).
- **Entities/VOs:** TaskProfile(VO), FallbackProfile(VO), PromptTemplate, MemoryRecord, Trace, GuardrailCheck(VO).
- **Commands:** `RegisterModel`, `RouteRequest`, `RegisterTool`, `RunEval`, `PromoteModel`, `RecordTrace`, `BindTaskProfile`.
- **Evt:** `ModelRegistered`, `ModelPromoted`, `ModelEvaluationFailed`, `ToolRegistered`, `GuardrailTriggered`, `FallbackInvoked`.
- **Sub:** `PolicyViolationDetected`, `KillSwitchActivated` (halts routing), `PrincipalRevoked`.
- **Policies/invariants:** (1) All model access via gateway (no direct vendor calls). (2) Every tool registered with schema + permission scope; unregistered tools uncallable. (3) Model promotion gated on eval thresholds + safety checks. (4) Every agent invocation traced. (5) On guardrail/eval failure → deterministic fallback or escalate, never silent.
- **Data ownership:** model registry, tool registry, eval sets/results, traces, prompt templates, agent memory.
- **APIs:** `POST /gateway/complete`, `POST /tools`, `GET /tools`, `POST /evals/run`, `POST /models/{id}/promote`, `GET /traces/{id}`.
- **Agent roster:** Model-Ops Agent, Eval Agent, Tool-Governance Agent, Prompt-Optimization Agent.
- **Human approval points:** promoting a new base model to production task profiles; registering a tool with money/PII/irreversible scope; raising an agent's authority level.
- **Compliance:** model cards + eval evidence; bias monitoring feeds Compliance; trace retention policy; PII redaction in traces.
- **Observability:** eval pass rate, hallucination/grounding metrics, latency/cost per task profile, fallback rate, drift.
- **Failure modes:** bad model output (evals + guardrails + fallback); vendor outage (multi-provider fallback profiles); prompt-template regression (versioned + eval-gated).
- **KPIs:** eval pass rate, grounded-output %, p95 latency, cost/task, fallback rate, drift alerts.

---

## 12. Knowledge Management

- **Purpose:** Curate authoritative, provenance-bearing knowledge sources for RAG grounding across the company.
- **Ubiquitous language:** Knowledge Artifact, Source of Truth, Provenance, Approval State, Freshness, Citation.
- **Subdomains:** knowledge curation (core), source approval/governance (core), retrieval indexing (supporting), freshness/decay (supporting).
- **Aggregates:** `KnowledgeArtifact` (content + provenance + approval), `KnowledgeCollection`, `SourceRegistration`.
- **Entities/VOs:** Provenance(VO), ApprovalState(VO), Citation, FreshnessWindow(VO), AccessScope(VO).
- **Commands:** `IngestArtifact`, `ApproveArtifact`, `DeprecateArtifact`, `IndexArtifact`, `RegisterSource`, `AttachProvenance`.
- **Evt:** `ArtifactIngested`, `ArtifactApproved`, `ArtifactDeprecated`, `ArtifactIndexed`, `SourceRegistered`.
- **Sub:** `FeatureShipped`, `TicketResolved`, `IncidentResolved`, `MetricDefined` (auto-ingest candidate knowledge).
- **Policies/invariants:** (1) Only approved artifacts are retrievable for customer-facing grounding. (2) Every artifact carries provenance + freshness. (3) Deprecated artifacts removed from retrieval immediately. (4) Access scope enforced (some knowledge internal-only). (5) External citations must be real + verifiable.
- **Data ownership:** knowledge artifacts, collections, source registry, approval state, provenance graph.
- **APIs:** `POST /artifacts`, `POST /artifacts/{id}/approve`, `POST /artifacts/{id}/deprecate`, `GET /artifacts/search`, `POST /sources`.
- **Agent roster:** Knowledge-Curation Agent, Source-Approval Agent, Freshness Agent.
- **Human approval points:** approving externally-sourced/regulated knowledge; designating a source authoritative; legal/medical content (pack-dependent).
- **Compliance:** provenance = grounding evidence; access-scope respects confidentiality; external citations verified (no fabrication).
- **Observability:** % approved retrievable, stale-artifact rate, citation-verification rate, retrieval hit quality.
- **Failure modes:** stale knowledge served (freshness decay + deprecation); unapproved content leaking to customers (approval gate); fabricated citation (verification step).
- **KPIs:** approved-coverage %, freshness compliance, grounding precision, citation validity.

---

## 13. Workflow Orchestration

- **Purpose:** Durable, observable orchestration of long-running, multi-context processes including approvals and sagas.
- **Ubiquitous language:** Workflow, Activity, Saga, Compensation, Approval Step, Timeout, Idempotency Key.
- **Subdomains:** durable workflow engine (core), approval orchestration (core), saga/compensation (core), scheduling (supporting).
- **Aggregates:** `WorkflowInstance` (state machine + history), `ApprovalRequest` (approvers + decision), `Saga` (steps + compensations).
- **Entities/VOs:** Activity, CompensationStep, ApprovalDecision(VO), Timeout(VO), IdempotencyKey(VO).
- **Commands:** `StartWorkflow`, `CompleteActivity`, `RequestApproval`, `RecordApproval`, `CompensateSaga`, `CancelWorkflow`.
- **Evt:** `WorkflowStarted`, `WorkflowCompleted`, `WorkflowFailed`, `ApprovalRequired`, `ApprovalGranted`, `ApprovalDenied`, `SagaCompensated`.
- **Sub:** `DecisionMade`, `PaymentFailed`, `DataSubjectRequestReceived`, `IncidentDetected` (workflow triggers).
- **Policies/invariants:** (1) Every irreversible step is preceded by its approval step or runs inside a compensable saga. (2) All activities idempotent. (3) Timeouts escalate, never silently drop. (4) Approval requests carry full context + authority-matrix reference. (5) Workflow history immutable + auditable.
- **Data ownership:** workflow state/history, approval requests, saga definitions, schedules.
- **APIs:** `POST /workflows`, `GET /workflows/{id}`, `POST /approvals/{id}/decide`, `POST /workflows/{id}/cancel`, `GET /approvals?assignee=`.
- **Agent roster:** Orchestration Agent (limited authority — executes defined workflows, cannot redefine them).
- **Human approval points:** the approval steps themselves are where humans act (DSAR fulfilment, payments, releases, etc.).
- **Compliance:** DSAR + breach workflows run here; approval records are evidence.
- **Observability:** workflow success/failure rate, approval latency, saga compensation rate, stuck-workflow count.
- **Failure modes:** stuck workflow (timeout + escalation); non-idempotent retry (idempotency keys); orphaned saga (compensation on failure).
- **KPIs:** workflow completion rate, approval SLA, compensation rate, mean workflow duration.

---

## 14. Experimentation & Growth

- **Purpose:** Run trustworthy experiments and growth loops; arbitrate what ships based on evidence.
- **Ubiquitous language:** Experiment, Hypothesis, Variant, Guardrail Metric, Statistical Significance, Growth Loop.
- **Subdomains:** experiment design (core), assignment/exposure (core), analysis/inference (core), growth-loop ops (supporting).
- **Aggregates:** `Experiment` (hypothesis, variants, metrics), `AssignmentUnit` (who sees what), `Result` (inference + decision).
- **Entities/VOs:** Hypothesis, Variant, GuardrailMetric(VO), SignificanceResult(VO), ExposureLog.
- **Commands:** `DesignExperiment`, `StartExperiment`, `AssignVariant`, `ConcludeExperiment`, `ShipWinner`, `AbortExperiment`.
- **Evt:** `ExperimentStarted`, `VariantAssigned`, `ExperimentConcluded`, `GuardrailBreached`, `WinnerShipped`.
- **Sub:** `FeatureShipped`, `SegmentEntered`, `MetricDefined`, `CampaignLaunched`.
- **Policies/invariants:** (1) No ship-decision without pre-registered hypothesis + primary metric. (2) Guardrail-metric breach auto-aborts. (3) Metrics resolve through the semantic layer (no bespoke math). (4) Assignment is consistent + logged. (5) No experimenting on protected/vulnerable cohorts without review.
- **Data ownership:** experiment definitions, assignments, exposure logs, results.
- **APIs:** `POST /experiments`, `POST /experiments/{id}/start`, `GET /experiments/{id}/results`, `POST /experiments/{id}/ship`.
- **Agent roster:** Experiment-Design Agent, Analysis Agent, Growth-Loop Agent.
- **Human approval points:** experiments touching pricing, legal terms, vulnerable cohorts, or safety-relevant flows.
- **Compliance:** lawful basis for experimentation on personal data; no dark-pattern experiments; consent respected.
- **Observability:** experiment velocity, guardrail-breach rate, false-positive rate, ship win rate.
- **Failure modes:** peeking/p-hacking (pre-registration + fixed analysis); guardrail miss (auto-abort); contaminated assignment (consistent hashing).
- **KPIs:** experiment throughput, win rate, guardrail safety, incremental lift shipped.

---

## 15. Vendor & Procurement

- **Purpose:** Source, onboard, govern, and offboard third-party vendors and tools within security/spend policy.
- **Ubiquitous language:** Vendor, DPA, Subprocessor, Spend Cap, Renewal, Risk Tier, Exit Path.
- **Subdomains:** sourcing/evaluation (core), onboarding/risk (core, security+privacy-critical), contract/renewal (core), spend governance (supporting).
- **Aggregates:** `Vendor` (profile + risk tier), `ProcurementRequest`, `VendorContract` (terms + renewal).
- **Entities/VOs:** RiskTier(VO), DPA(VO), Subprocessor, SpendCommitment(VO), ExitPath(VO).
- **Commands:** `RequestVendor`, `AssessVendorRisk`, `OnboardVendor`, `SignVendorContract`, `RenewContract`, `OffboardVendor`.
- **Evt:** `VendorRequested`, `VendorRiskAssessed`, `VendorOnboarded`, `VendorContractSigned`, `ContractRenewal`, `VendorOffboarded`.
- **Sub:** `BudgetThresholdExceeded`, `PolicyViolationDetected`, `SecurityFindingRaised`.
- **Policies/invariants:** (1) No vendor processing personal data without a DPA + subprocessor entry in RoPA. (2) Security risk assessment required before onboarding. (3) Spend above cap requires approval. (4) Every vendor has a documented exit path (per open-source policy). (5) Auto-renewals flagged before commit.
- **Data ownership:** vendor profiles, contracts, risk assessments, subprocessor list, spend commitments.
- **APIs:** `POST /vendors`, `POST /vendors/{id}/risk`, `POST /vendors/{id}/onboard`, `POST /contracts`, `GET /subprocessors`.
- **Agent roster:** Sourcing Agent, Vendor-Risk Agent, Contract Agent.
- **Human approval points:** onboarding a personal-data processor; spend above cap; multi-year/lock-in contracts; high-risk-tier vendors.
- **Compliance:** subprocessor register feeds RoPA; DPA enforcement; cross-border transfer review with Compliance.
- **Observability:** vendor risk-tier distribution, renewal lead time, spend vs budget, DPA coverage.
- **Failure modes:** shadow vendor (procurement gate + spend monitoring); missing DPA (onboarding block); lock-in (exit-path requirement).
- **KPIs:** % vendors with DPA, spend-vs-budget, risk-tier mix, renewal savings, exit-path coverage.

---

## 16. People & Workforce

- **Purpose:** Manage the (small) human workforce and the human↔agent collaboration model: roles, approvals duty roster, training, access lifecycle.
- **Ubiquitous language:** Worker, Role, Approval Duty, Access Lifecycle, Onboarding, Capability.
- **Subdomains:** human roster/roles (core), approval-duty assignment (core, governance-critical), access lifecycle (core, security-linked), capability/training (supporting).
- **Aggregates:** `Worker` (person + role), `ApprovalDuty` (who approves what, when), `AccessGrant` (lifecycle).
- **Entities/VOs:** Role, Capability(VO), DutyRoster, OnboardingTask, OffboardingTask.
- **Commands:** `OnboardWorker`, `AssignRole`, `AssignApprovalDuty`, `GrantAccess`, `RevokeAccess`, `OffboardWorker`.
- **Evt:** `WorkerOnboarded`, `RoleAssigned`, `ApprovalDutyAssigned`, `AccessGranted`, `AccessRevoked`, `WorkerOffboarded`.
- **Sub:** `ApprovalRequired` (route to on-duty human), `PrincipalRevoked`, `IncidentDetected`.
- **Policies/invariants:** (1) Every approval-required action maps to a named human on duty (no orphan approvals). (2) Offboarding revokes all access within SLA. (3) Separation-of-duties respected in duty assignment (maker ≠ checker). (4) Personal HR data minimized + access-restricted.
- **Data ownership:** worker records, roles, duty rosters, access grants, training records.
- **APIs:** `POST /workers`, `POST /workers/{id}/roles`, `POST /approval-duties`, `POST /access-grants`, `POST /workers/{id}/offboard`.
- **Agent roster:** Onboarding Agent, Duty-Roster Agent, Access-Lifecycle Agent. (CHRO Agent in Executive.)
- **Human approval points:** hiring/termination; granting high-privilege roles; HR-sensitive actions.
- **Compliance:** employee data is personal data (employment basis); access lifecycle ties to Security; HR retention rules.
- **Observability:** approval-coverage (no orphan approvals), offboarding-revocation SLA, duty-roster completeness.
- **Failure modes:** orphan approval (duty-roster guardrail + escalation chain); stale access after offboarding (automated revocation saga).
- **KPIs:** approval coverage, offboarding SLA, separation-of-duties compliance, training currency.

---

### Cross-context dependency summary

Every edge in `01_context_map.mermaid` is a **published API**, a **domain event (PL)**, or an **explicit ACL** — no context reads another's private store. Mandatory ACLs: Sales←Marketing (consent semantics), Finance←Sales (deal→ledger), CS←Data (health scores), Executive←Data/Finance (metrics), Vendor/People←Finance (spend/payroll). The **Subject Rights API** (context 9) is a Conformist contract every personal-data context must implement.
