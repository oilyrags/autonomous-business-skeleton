# business_skeleton.md — Minimum Viable Autonomous Business Skeleton

The smallest useful first build: enough to run **one** venture end-to-end, safely and auditably, on a reusable base. Everything here is required for the MVP; the deferral list states what is intentionally left out and why.

## 1. What the MVP includes (and which artifact specifies it)

| Capability | Why it's in the MVP | Spec |
|---|---|---|
| **Identity & access control** | Every action must be authenticated/authorized | `10` |
| **Agent registry** | Agents are accountable principals, not scripts | `05` |
| **Model gateway** | Vendor-swappable, deterministic fallbacks, no direct calls | `11` |
| **Tool registry** | Unregistered tools uncallable; scopes enforced | `11` |
| **Event bus** | Only async integration path; Redpanda + AsyncAPI | `04`, `events.asyncapi.yaml` |
| **Audit log** | Immutable evidence backbone | `10` |
| **Policy engine** | Authorization + purpose-limitation as code (OPA) | `09`, `10` |
| **Data inventory** | No personal data without an entry | `08` |
| **Consent model** | Lawful basis, synchronous suppression | `09`, `03` CRM |
| **DSAR workflow** | Rights propagate across all personal-data contexts | `09` |
| **Canonical entities** | Customer, Product, Invoice, Ticket, Decision, AuditEvent | `07` |
| **Product engineering pipeline** | Spec→codegen→tests→CI/CD→rollback | `03` Product, `15` |
| **Basic CRM & sales workflow** | Lead→consent→qualify→quote (maker-checker) | `03` CRM/Sales |
| **Basic billing & finance controls** | Double-entry ledger, deterministic billing, capped maker-checked payments | `03` Finance, `06` |
| **Basic customer support workflow** | Grounded answers, escalation, DSAR routing | `03` CS |
| **Data warehouse / lakehouse** | Iceberg + medallion | `12` |
| **Semantic metric layer** | One definition per KPI (Cube) | `12`, `13` |
| **Decision records** | Material decisions are auditable | `13` |
| **Autonomy authority matrix** | Every process has a level + controls | `06` |
| **Kill switch** | Launch blocker; global/context/agent | `10` |
| **Verification suite** | 12 audits + failure injection | `16` |

## 2. MVP end-to-end slice (the proof)

The MVP must run the `14` worked example slice — **Build → Market → Sell → Bill → Serve → Learn** — for a single B2B SaaS venture, using only the systems above and these named human approvals: DPIA sign-off, launch approval (CEO+CISO), contract execution (legal), above-cap/new-payee payments (Finance maker-checker), above-threshold discounts (Deal-Desk). When that slice passes audits 5/6/7 and the kill-switch drill, the MVP is accepted.

## 3. MVP autonomy posture

- Most agents at **L2–L3** (recommend / execute-after-approval).
- L4 only where deterministic + capped: standard invoicing, grounded support answers, DSAR routing, consent enforcement.
- **No L5. No autonomous money movement beyond caps. No autonomous legal commitments.**

## 4. Explicitly deferred (with rationale, risk, inclusion trigger)

| Deferred | Why | Risk of deferral | Include when |
|---|---|---|---|
| Compliance packs beyond GDPR + finance-core (health, payments, children, etc.) | Avoid over-building for industries not yet entered | Cannot enter regulated verticals yet | A venture targets that vertical (gate 7) |
| Full agentic C-suite (all 12) | MVP needs CEO/CFO/CPO/CMO/CISO/CLO; others can be stubbed | Thinner cross-functional arbitration | Phase 7 / 2nd venture |
| Knowledge graph (Neo4j/AGE) | Vector RAG suffices for MVP grounding | Less relational reasoning | Decision-intelligence depth needed |
| Multi-region active-active residency | Single EU primary + documented transfers is enough | Limited geographic expansion | Cross-border scale (Compliance review) |
| MMM / advanced attribution | Simple attribution + experiments suffice early | Coarser spend optimization | Spend scale justifies it |
| Feature store (Feast) | No production ML features at MVP | Manual feature handling | First production ML model |
| Treasury automation, AP at scale | Low transaction volume early | Manual treasury ops | Cash/vendor volume grows |
| Red-team agent + scheduled audits | Manual review acceptable at MVP scale | Slower detection of control drift | Phase 9 / before scaling autonomy |
| L4/L5 uplifts for any process | Safety-first; prove controls first | Slower autonomy gains | Failure-injection clean + uplift decision (`06`) |

## 5. Acceptance (MVP)

Accepted when: all 20 capabilities are live; the end-to-end slice runs; audits 1–11 are PASS/CONDITIONAL with conditions met for the MVP surface; audit 12 failure-injection suite runs and findings are remediated; kill-switch drill passes within SLA; every personal-data element in the slice has an `08` entry; every money-moving action is capped + maker-checked. Deferred items are tracked with their inclusion triggers above.

---

### Package index
`00` overview · `01` context map · `02` glossary · `03` domain catalog · `04`/`events.asyncapi.yaml` events · `05` agent registry · `06` authority matrix · `07` data model · `08` data inventory · `09` compliance · `10` security · `11` model/agent · `12` tech stack · `13` decision OS · `14` instantiation · `15` roadmap/backlog · `16` verification · `business_skeleton.md` (this file).
