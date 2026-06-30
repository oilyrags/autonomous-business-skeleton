# 06 — Autonomy Authority Matrix

This matrix is the binding control surface. Every agent action references a row here (events carry `authorityMatrixRef`). No process exceeds its assigned level without a documented uplift decision.

## Autonomy levels

| Level | Name | Meaning |
|---|---|---|
| **L0** | Manual | Humans do it; AI not involved. |
| **L1** | AI assists | AI augments a human who acts. |
| **L2** | AI recommends | AI proposes; human decides and executes. |
| **L3** | AI executes after approval | AI prepares and executes only after explicit approval. |
| **L4** | AI executes autonomously within policy | AI acts within hard policy/caps; logged + reversible/monitored. |
| **L5** | AI optimizes autonomously | AI runs closed control loops within audited, policy-bounded limits. |

## Decision classification dimensions

Each process is scored on: **financial impact, legal impact, privacy impact, reversibility, customer-harm potential, brand/reputation risk, security risk, regulatory exposure, model confidence, data quality.** High exposure on any single dimension caps the feasible level downward regardless of others (the *minimum rule*).

## Process matrix

| # | Process | Target L | Feasible v1 L | Risk class | Approval threshold / trigger | Required controls | Rollback | Evidence |
|---|---|---|---|---|---|---|---|---|
| AM-01 | Lead capture & enrichment | L4 | L4 | low (privacy) | new lawful-basis category | lawful-basis check, consent record | suppress/erase | consent log, audit event |
| AM-02 | Consent grant/revoke enforcement | L4 | L4 | high (privacy/legal) | none (deterministic) | synchronous suppression, immutable record | n/a (append-only) | consent_retention store |
| AM-03 | Campaign launch (standard) | L4 | L3 | medium (brand/privacy) | spend>cap, large audience, new data use, brand-risk | claim-check, suppression, spend cap | pause campaign | campaign + approval record |
| AM-04 | Paid budget reallocation | L3 | L2 | high (financial) | any reallocation > threshold | maker-checker, cap, decision record | revert allocation | decision record |
| AM-05 | Lead qualification (MEDDIC/BANT) | L4 | L4 | low | — | scoring model, logged rationale | re-qualify | audit event |
| AM-06 | Quote creation (standard pricing) | L4 | L3 | medium (financial/legal) | discount>threshold, non-standard terms | deterministic pricing, maker≠checker | void quote | quote record |
| AM-07 | Quote/discount approval | L2 | L2 | high (financial/legal) | always (this *is* the checker step) | separation of duties | n/a | approval record |
| AM-08 | Contract execution | L2 | L0/L2 | high (legal) | always — human/legal counsel | legal review gate, CLO escalation | n/a (binding) | signed contract, review log |
| AM-09 | Invoice issuance (standard) | L4 | L4 | medium (financial) | manual adjustment, credit>cap | deterministic billing, idempotency | credit note (maker-checker) | InvoiceIssued, ledger |
| AM-10 | Ledger posting | L4 | L4 | high (financial) | manual adjustment, write-off | append-only, balanced, deterministic | reversing entry (maker-checker) | LedgerEntryPosted (immutable) |
| AM-11 | Payment / money movement | L3 | L3 | critical (financial) | **every payment** above cap; new payee always | hard spend cap, maker-checker, allow-list payees | reversal where possible | approval + payment record |
| AM-12 | Revenue recognition | L4 | L4 | high (financial/legal) | revrec policy change | deterministic schedule engine | adjusting entry | RevenueRecognized, schedule |
| AM-13 | Refund / goodwill credit | L4 | L3 | medium (financial/customer) | above cap | cap, maker-checker via Finance | reverse credit | RefundProposed + approval |
| AM-14 | Support answer (grounded) | L4 | L4 | medium (customer) | uncertainty, regulated/safety/vulnerable | grounding gate, entitlement check, escalate-on-uncertainty | edit/retract answer | ticket + grounding trace |
| AM-15 | DSAR fulfilment (access/port.) | L4 | L4 | high (privacy/legal) | identity edge cases, deadline ext. | subject-rights saga, evidence store | n/a | DSAR record + export proof |
| AM-16 | DSAR erasure | L4 | L3 | high (privacy/legal) | legal-hold conflict | propagation saga, legal-hold check | n/a (irreversible by design) | DataDeletionCompleted + exclusions |
| AM-17 | Code generation & PR | L4 | L3 | medium (security/quality) | merge to main, new dep, breaking change | tests+scans gate, code review | revert PR | PR + scan results |
| AM-18 | Production release promotion | L3 | L3 | high (reliability) | high-risk release, schema change | green-gate, progressive delivery | automatic rollback | ReleasePromoted + gate proof |
| AM-19 | Incident response (containment) | L4 | L4 | high (reliability/security) | external comms, Sev1 customer impact | runbook, blast-radius limit | n/a | incident record + postmortem |
| AM-20 | Experiment ship decision | L4 | L3 | medium | pricing/legal/vulnerable cohorts | pre-registration, guardrail auto-abort | unship variant | experiment result record |
| AM-21 | Metric definition (non-board) | L3 | L3 | low | board KPI, sensitivity reclass | single-definition rule, review | revert definition | MetricDefined |
| AM-22 | Capital allocation | L3 | L2 | critical (financial/strategy) | above threshold, venture kill | board envelope, decision record | reverse where possible | decision + CapitalAllocated |
| AM-23 | Vendor onboarding (PII processor) | L3 | L2 | high (privacy/security) | always for PII processors | DPA, risk assessment, subprocessor entry | offboard | risk assessment + DPA |
| AM-24 | Circuit-breaker trip | L4 | L4 | high (security) | global kill-switch (human) | scoped containment | re-enable after review | security audit event |
| AM-25 | Global kill-switch activation | L3 | L3 | critical (security) | **always human-approved**; any agent may *request* | dual-control deactivation | controlled restart | KillSwitchActivated record |
| AM-26 | Hiring / termination | L2 | L0 | high (legal/HR) | always — human | HR review, access lifecycle | n/a | HR record |
| AM-27 | Strategy pivot | L2 | L2 | critical (strategy) | always — human board | decision record, dissent capture | re-plan | decision record |

## The minimum rule (worked)

A process's feasible level is `min(level allowed by each dimension)`. Example — **AM-11 Payment**: financial=critical → cap L3; legal=high → L3; reversibility=low → L2 for above-cap. Result: **payments execute at L4 only within a pre-authorized cap + allow-listed payee; everything else is L3 (approval) or lower.** No payment path is ever L5.

## Uplift governance

- Raising any process's level is itself a **material decision** (decision record + CISO + CLO sign-off + 30-day monitored trial).
- L5 is reserved for **closed loops with no money/legal/irreversible exposure** (e.g. ad-bid micro-optimization within a hard daily cap, content-format A/B selection) and requires audited control-loop bounds + a kill switch.
- Any failure-injection finding (`16`) that shows a control gap auto-demotes the affected process one level until remediated.
