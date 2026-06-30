# 14 — Instantiation Guide (Productization Layer)

How a new business idea becomes a running venture **on the existing skeleton** without rebuilding it. A venture is a configuration + a thin set of idea-specific artifacts on top of the shared contexts.

## 1. What a venture inherits vs. what it adds

| Inherited (skeleton, reused) | Added per venture (configured/authored) |
|---|---|
| All 16 bounded contexts + agent platform | Venture config (market, compliance packs, autonomy targets) |
| Event backbone, APIs, workflows | Product specs + feature set |
| Identity, policy engine, kill switch, audit | ICP/segments, price book, consent purposes |
| Data fabric, semantic layer, decision OS | Venture-specific metrics (mapped to canonical defs) |
| Subject Rights API, compliance core | Data inventory entries (`08`) for new personal data |
| Finance ledger, billing engine | Chart-of-accounts mapping, billing plans |

## 2. Instantiation stages (gated pipeline)

Each stage is a Workflow with a gate; failing a gate halts the venture.

| Stage | Activity | Owner agent | Gate |
|---|---|---|---|
| 1. Idea intake | Capture idea, hypothesis, sponsor | CEO/CPO | clear problem + hypothesis |
| 2. Market research | TAM/SAM/SOM, trends, competition | CPO + Data | evidence-backed market size |
| 3. ICP validation | Define ideal customer, JTBD | CMO + CPO | validated ICP |
| 4. Competitive analysis | Five Forces, positioning | CEO + CMO | defensible position |
| 5. Financial model | Unit economics, three-statement, DCF | CFO | LTV:CAC + payback within policy |
| 6. Risk assessment | Risk register, autonomy targets | CISO + COO | risks owned + mitigations |
| 7. Legal & compliance review | Lawful basis, DPIA triggers, pack selection | CLO + DPO (human) | **DPIA signed if triggered; gate** |
| 8. Product prototype | Spec + ADRs | CPO + Product | spec approved |
| 9. MVP build | Code-gen + tests + CI/CD | Product + QA | green gates, reversible |
| 10. Data instrumentation | Inventory entries, metrics, contracts | CDO + Data | metrics canonical, PII classified |
| 11. GTM setup | Segments, consent purposes, campaigns | CMO | lawful-basis configured |
| 12. Support readiness | Knowledge base, entitlements, escalation | CCO | grounded answers ready |
| 13. Billing setup | Plans, price book, revrec policy | CFO | deterministic billing tested |
| 14. Experiment plan | Hypotheses, guardrail metrics | Growth | pre-registered experiments |
| 15. Launch gate | All gates green + kill switch verified | CEO + CISO | **launch approval (human)** |
| Post | Scale / pivot / kill criteria | CEO portfolio review | quarterly gate |

**Scale / pivot / kill criteria** (set at launch, reviewed quarterly): e.g. scale if payback < target & retention > threshold for 2 cohorts; pivot if activation < floor but demand signal strong; kill if unit economics negative with no path after N cycles. Recorded as a `Decision`.

---

## 3. Worked example — "InboxIQ" (B2B SaaS: AI email-triage for SMB support teams)

A full pass through **Build → Market → Sell → Bill → Serve → Learn** using only defined systems and explicit approval paths.

### Build
- **Intake → Compliance review:** Idea logged; processes customer support emails (personal data). CLO Agent flags processing of personal data + profiling → **`DPIARequired`**; DPO signs DPIA before build go-live (gate 7). Compliance pack: GDPR core (no special-category). Lawful basis: `contract` (service) + `legitimate_interest` (triage), LIA stored.
- **Spec → MVP:** CPO Agent writes spec (SpecApproved); Code-Gen Agent builds the triage service + Subject Rights API consumer; tests + security/license scans green (no-green-no-ship); `ReleasePromoted` via progressive delivery with rollback. Inventory entries added to `08` for ingested email content (`support_retention`, anonymize-on-erase).

### Market
- CMO Agent defines ICP (SMB support leads, 5–50 agents) and segments. Consent purposes configured. Campaign Agent launches a content + email campaign — **only to contacts with valid lawful basis**; suppression enforced synchronously. Spend within cap; above-cap reallocation would require CFO approval (AM-04). `CampaignLaunched`, `LeadCaptured`, `ConsentGranted` flow to Data + Sales.

### Sell
- Lead-Routing + Qualification Agents qualify via MEDDIC (`OpportunityQualified`). CPQ Agent issues a standard quote from the price book (`QuoteIssued`); a 30% discount request exceeds threshold → **Deal-Desk approval** (AM-06/07, maker≠checker). On signature, Contract execution is human/legal (AM-08) → `ContractSigned`, `DealWon`.

### Bill
- `DealWon` → Billing Agent issues invoice deterministically (`InvoiceIssued`, AR debit / deferred revenue). Customer pays → `PaymentReceived` (cash debit / AR credit, idempotent). Revrec engine recognizes ratably (`RevenueRecognized`). All postings append-only to the ledger; any manual adjustment is maker-checker (AM-09/10). No agent moves money beyond the pre-authorized rules.

### Serve
- Customer support questions arrive as tickets. Support-Answer Agent answers **grounded in approved KnowledgeArtifacts** with citations; uncertain → escalate (AM-14). A user emails a deletion request → **routed to Compliance DSAR workflow** (not answered ad hoc): saga fans out to CRM, CS, Finance (erasure blocked by financial 10y obligation, itemized), Data, AI memory → `DataDeletionCompleted` with exclusions + evidence.

### Learn
- Growth Agent runs a pre-registered experiment on onboarding (guardrail: activation must not drop); winner shipped (`ExperimentConcluded`, `WinnerShipped`). Finance + Data report cohort unit economics to Executive. CEO Agent opens a `Decision`: payback 8mo < 9mo target & retention healthy → **scale** Segment A budget (the AM-04/AM-22 decision shown in `13`); CFO records dissent on runway sensitivity; review date set; outcome reviewed next quarter (learning loop).

### What required humans (named)
- DPIA sign-off (DPO), launch approval (CEO+CISO), contract execution (legal counsel), above-threshold discount (Deal-Desk human approver), any money movement above cap / new payee (Finance maker-checker), regulator/subject breach notification (if it had occurred).

This proves the skeleton runs a venture end-to-end with personal-data flows inventoried, money capped + maker-checked, every agent action logged/revocable, and a verified kill switch.
