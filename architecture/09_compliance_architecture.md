# 09 — Compliance Architecture (compliance-by-construction)

GDPR-first. **We do not claim legal certainty.** We build mechanisms that produce *provable compliance readiness*: automated controls, evidence, audit logs, legal-review gates, DPIAs, DSAR workflows, policy-as-code, and jurisdiction config. Where judgment is legally significant, a named human/role decides.

## 1. Control model

```
Policy-as-Code (OPA/Cedar)  ──▶ enforced at: API gateway, event publish, tool call, release gate
Data Inventory (08)         ──▶ generates RoPA; gates personal-data processing
Subject Rights API (mandatory) ──▶ implemented by every personal-data context
Evidence Store (append-only) ──▶ holds DPIAs, approvals, eval results, fulfilment proofs
DPIA Engine                 ──▶ triggered by rules; blocks high-risk go-live until signed
Consent Service             ──▶ system of record in CRM; enforced synchronously pre-action
```

## 2. Lawful basis & purpose limitation

- No personal data is processed without (a) a `08` inventory entry and (b) a lawful basis from {consent, contract, legitimate_interest, legal_obligation, vital_interest, public_task}.
- **Purpose limitation enforced in policy:** a tool/query requesting a personal field must declare a purpose; OPA checks the purpose against the inventory entry's allowed purposes. Mismatch → deny + `PolicyViolationDetected`.
- `legitimate_interest` requires a stored LIA (Legitimate Interest Assessment); objection must be supported.

## 3. Subject Rights API (mandatory contract)

Every context owning personal data implements the **consumer side** of this contract; Compliance orchestrates the saga across all of them.

```
POST /subject-rights/access      → returns all personal data held for subject (provenance-tagged)
POST /subject-rights/erasure     → delete/anonymize unless legal_obligation/legal_hold; confirm
POST /subject-rights/portability → machine-readable export of subject-provided data
POST /subject-rights/rectify     → correct inaccurate data; propagate
POST /subject-rights/object      → stop legitimate_interest processing for subject
POST /subject-rights/restrict    → freeze processing pending resolution
GET  /subject-rights/status/{dsarId} → per-context fulfilment state
```

**DSAR saga (Workflow context):**
1. `DataSubjectRequestReceived` → identity verification → fan-out to all personal-data contexts (from `08`).
2. Each context processes and returns confirmation + evidence.
3. **Completeness check:** saga will not emit `DataDeletionCompleted` until *every* mapped context confirms (or records a legal-hold exclusion).
4. Statutory clock tracked (default ≤30 days, extension path with approval).
5. Evidence (per-context confirmations, exclusions) written to evidence store.

> Erasure conflict rule: financial records under `legal_obligation` (10y) and any `legal_hold` override erasure; the response itemizes retained data + the basis. This is by design and surfaced to the subject.

## 4. DPIA triggers (automated)

A `DPIARequired` event fires (blocking go-live) when a new processing activity matches any trigger:
- Large-scale processing of personal data, or any special-category data.
- Systematic monitoring / profiling that informs significant automated decisions.
- New automated decision-making with legal/similar effect (Art.22).
- New cross-border transfer, new high-risk vendor (PII processor), or new compliance pack enabling sensitive data.

DPIA must be human-signed (DPO/CLO) before the activity goes live; the DPIA is stored as evidence.

## 5. AI transparency & significant-automated-decision handling

- Every `AgentDecisionMade` is screened (`art22Significant` flag) against rules: does it produce a legal or similarly significant effect on a natural person (e.g. credit-like decisions, denial of service, pricing affecting an individual)?
- If significant: (a) a transparency notice explains the logic and consequences; (b) a **human-review path** is offered; (c) the decision is logged with its data + reasoning provenance; (d) it cannot run at L4/L5 — capped at L3 with human in the loop.
- **Bias monitoring:** the AI Platform runs fairness evals on models used in significant decisions; results to evidence store; failures block promotion.

## 6. Consent & ePrivacy

- Consent Service (CRM system of record) stores grant/revoke per channel+purpose with timestamps (immutable log).
- `ConsentRevoked` is enforced **synchronously before the next action** (suppression check is a hard pre-send guardrail), and propagates to Sales, CS, Data, AI Platform.
- Cookie/tracking consent handled at edge; analytics events tagged with consent state; non-consented analytics dropped.

## 7. Retention, residency, cross-border

- Retention rules in `08`; a retention job anonymizes/deletes on schedule, honoring legal holds.
- Default residency EU; `crossBorderTransfer != none` requires a documented mechanism (adequacy/SCC) + Compliance review + RoPA note.

## 8. Contract review, breach response, regulator-readiness

- **Contract review:** CLO Agent drafts redlines (L2); execution is always human/legal (AM-08).
- **Breach response:** `IncidentDetected` involving personal data → Compliance breach-assessment within SLA → `BreachDeclared` if thresholds met → regulator/subject notification is human-approved → all steps evidenced; 72-hour clock tracked.
- **Regulator-ready evidence store:** RoPA (generated from `08`), DPIAs, DSAR fulfilment proofs, consent logs, policy versions, audit log, eval results — all queryable, append-only.

## 9. Compliance packs (optional, off by default)

| Pack | Adds |
|---|---|
| finance | SOX-lite change control, stronger SoD, financial-records 10y |
| health | special-category data handling, HIPAA/EU-health rules, stricter access |
| employment | worker-rights, monitoring limits |
| public_sector | public_task basis, transparency, accessibility (WCAG) escalation |
| children | age verification, parental consent, no profiling |
| payments | PCI-DSS scope isolation, tokenization |
| insurance | suitability, fair-pricing, conduct rules |

Each pack is a bundle of: extra inventory rules, extra OPA policies, extra approval thresholds, extra DPIA triggers. Enabling a pack is a material decision.

## Guardrails (binding)

1. No personal data without lawful basis + inventory entry.
2. Erasure propagates per policy and is evidenced (or legal-hold itemized).
3. Compliance gates block release (`ComplianceGateBlocked`).
4. Never claim legal certainty — produce evidence, controls, and a human-review mechanism.
