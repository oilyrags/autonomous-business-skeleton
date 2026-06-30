# PROJECT — Autonomous AI-First Business Skeleton

> **Purpose of this file:** single source of truth for project state. Read this first if you are a new model/session picking up the work. It captures what we're building, what's decided, what's done, what's pending, and the conventions to follow — so context survives model switches. **Keep it updated as work progresses** (see "How to maintain" at the bottom).

- **Last updated:** 2026-06-30 (agent registry expanded to full roster)
- **Updated by:** Claude (Opus 4.8)
- **Working directory:** `/Users/cliada/Documents/code/projects/autonomous-business`
- **Git repo:** yes — `main` branch, remote `origin` → https://github.com/oilyrags/autonomous-business-skeleton.git

---

## 1. What this project is

Designing the **operating system of an AI-run business**: a reusable, domain-driven architecture skeleton on which many business ideas can be launched, operated, scaled, pivoted, or shut down without rebuilding the foundation. AI-first, open-source-preferred, privacy-preserving (GDPR-first), audit-ready, deterministic where it must be (money/identity/access/consent/irreversible actions).

**Source of requirements:** [`autonomous-business-architecture-merged-prompt.md`](autonomous-business-architecture-merged-prompt.md) — the master prompt defining the full target output, schemas, bounded contexts, deliverables, verification suite, and acceptance criteria. This is the spec; treat it as authoritative.

---

## 2. Key decisions (locked)

| Decision | Choice | Date | Notes |
|---|---|---|---|
| Execution mode | **Mode B — Build Specification** | 2026-06-30 | Machine-readable contracts, schemas, testable acceptance criteria. (Modes A/C not used.) |
| Build approach | **Consolidated architect pass** (single model, no multi-agent fan-out) | 2026-06-30 | User chose this over full multi-agent workflow and over core-only. Concise per artifact, complete coverage. |
| Output location | `architecture/` subdirectory | 2026-06-30 | All 19 artifacts live there. |
| Regulatory baseline | GDPR-first; finance pack as core; other packs deferred | per spec | |
| Worked-example venture | "InboxIQ" (B2B SaaS, AI email-triage for SMB support) | 2026-06-30 | Used in `14_instantiation_guide.md` |
| Agent registry scope | **Full roster — 72 agents across all 16 contexts** (registry v2.0) | 2026-06-30 | Expanded from the initial representative 22. Validated: all required fields, no dup ids, matches `rosterSummary`. |

---

## 3. Status overview

**Phase: Architecture design package — COMPLETE (v1.0).** Implementation has NOT started (these are design artifacts, not running code).

| # | Artifact (in `architecture/`) | Status | Notes |
|---|---|---|---|
| 00 | `00_enterprise_overview.md` | ✅ Done | Framing, scope assumptions, doctrine |
| 01 | `01_context_map.mermaid` | ✅ Done | 16 contexts, DDD relationships |
| 02 | `02_ubiquitous_glossary.md` | ✅ Done | Single language source |
| 03 | `03_domain_catalog.md` | ✅ Done | All 16 contexts, full DDD model |
| 04 | `04_event_catalog.md` | ✅ Done | ~70 events indexed |
| 04 | `events.asyncapi.yaml` | ✅ Done | AsyncAPI 3.0, validated |
| 05 | `05_agent_registry.json` | ✅ Done (full roster, v2.0) | Valid JSON; 72 agents, all 16 contexts |
| 06 | `06_autonomy_authority_matrix.md` | ✅ Done | 27 processes, L0–L5 |
| 07 | `07_data_model.md` | ✅ Done | 40 canonical entities |
| 08 | `08_data_inventory_template.json` | ✅ Done | Valid JSON; RoPA seed (8 sample records) |
| 09 | `09_compliance_architecture.md` | ✅ Done | GDPR/DSAR/DPIA/consent |
| 10 | `10_security_architecture.md` | ✅ Done | Zero-trust, kill switch |
| 11 | `11_model_and_agent_architecture.md` | ✅ Done | Gateway, evals, grounding |
| 12 | `12_tech_stack.md` | ✅ Done | OSS-first + exit paths |
| 13 | `13_decision_operating_system.md` | ✅ Done | Decision registry + cadences |
| 14 | `14_instantiation_guide.md` | ✅ Done | Worked example end-to-end |
| 15 | `15_implementation_roadmap.md` | ✅ Done | 9 phases + sample backlog |
| 16 | `16_verification_report.md` | ✅ Done | 12 audits run |
| — | `business_skeleton.md` | ✅ Done | MVP + deferrals |

**Verification result (from `16`):** Accepted as buildable Mode-B design. **0 open design gaps.** **5 of 12 audits are CONDITIONAL** — they require build-time proof (running code), not design changes:
- Audit 4 (compliance lawful-basis): CI check that personal data has an `08` entry.
- Audit 6 (security): kill-switch drill within SLA; prompt-injection/exfiltration tests.
- Audit 7 (finance): ledger-balance invariant; double-payment failure-injection; maker-checker.
- Audit 9 (AI): eval gate blocks a bad model; grounding threshold; bias evals for Art.22.
- Audit 12 (failure-injection): run the scenario suite, remediate findings.

---

## 4. What needs to be done (pending / next steps)

### Open follow-ups on the design (optional, not blocking)
- [x] **Expand `05_agent_registry.json`** to the full agent roster across all 16 bounded contexts. — *done 2026-06-30, registry v2.0, 72 agents, validated.*
- [ ] **Thin-artifact assessment (2026-06-30):** package meets all acceptance minimums. Two intentionally-representative (not exhaustive) spots remain, both noted in-file and deferrable until build:
  - `events.asyncapi.yaml` — full message schemas for ~9 of ~70 events (rest indexed in `04_event_catalog.md`). Expand all 70 on request.
  - `15_implementation_roadmap.md` — 6 representative backlog stories rather than full per-phase backlog. This is implementation-prep (overlaps the "Phase 1 build plan" option); expand when build starts.
- [ ] Consider rendering `01_context_map.mermaid` to an image for stakeholders.

### If/when implementation starts (follows `15_implementation_roadmap.md`)
- [ ] **Phase 1 — Foundations:** identity (Keycloak/Zitadel), OPA, Vault, Redpanda + AsyncAPI registry, immutable audit log, **kill switch (launch blocker)**, GitOps repo standards.
- [ ] **Phase 2 — Core data:** canonical model, data inventory, Iceberg lakehouse, dbt, Cube semantic layer, catalog/lineage, classification-at-ingestion.
- [ ] **Phase 3 — Agent platform:** model gateway, tool registry, agent identity, memory, eval harness + Langfuse, OTel tracing.
- [ ] **Phase 4 — Product factory** → **5 CRM/Sales/Support** → **6 Finance & compliance** → **7 C-suite & Decision OS** → **8 Portfolio operation** → **9 Continuous optimization.**
- [ ] **Close the 5 CONDITIONAL audits** with the build-time proofs listed in section 3 above.

### Decisions still needed from the user (when relevant)
- Whether to initialize a git repo for the project.
- Whether/when to begin implementation vs. keep iterating on design.
- Target first real venture (the design used "InboxIQ" as an example only).

---

## 5. Conventions & doctrine (so work stays consistent)

- **Spec is law:** [`autonomous-business-architecture-merged-prompt.md`](autonomous-business-architecture-merged-prompt.md) governs structure, schemas, and acceptance criteria.
- **Mode B output:** prefer machine-readable contracts (Markdown/JSON/YAML/Mermaid/AsyncAPI/JSON-Schema), testable criteria.
- **DDD discipline:** each bounded context owns its data; integration only via published API, async domain event, or explicit ACL. No context reads another's private store.
- **Determinism boundary:** LLMs reason/draft/recommend; deterministic systems do money, ledger, permissions, policy enforcement, contractual gates. Never LLM math on financial paths.
- **Compliance honesty:** never claim legal certainty — design for *provable readiness* (controls, evidence, audit, human/legal review gates).
- **Autonomy:** default human-on-the-loop; human-in-the-loop for high-risk/irreversible/legally-significant/threshold-exceeding actions. No L5 for money/legal/irreversible. Kill switch is a launch blocker.
- **No fabricated citations or numbers.**
- **File naming:** keep the `NN_name.ext` numbering in `architecture/`; update both the artifact and this PROJECT.md when something changes.

---

## 6. File map

```
autonomous-business/
├── PROJECT.md                                          ← you are here (project tracker)
├── autonomous-business-architecture-merged-prompt.md   ← the master spec (requirements)
└── architecture/                                       ← the deliverable package (19 files)
    ├── 00_enterprise_overview.md
    ├── 01_context_map.mermaid
    ├── 02_ubiquitous_glossary.md
    ├── 03_domain_catalog.md
    ├── 04_event_catalog.md
    ├── events.asyncapi.yaml
    ├── 05_agent_registry.json
    ├── 06_autonomy_authority_matrix.md
    ├── 07_data_model.md
    ├── 08_data_inventory_template.json
    ├── 09_compliance_architecture.md
    ├── 10_security_architecture.md
    ├── 11_model_and_agent_architecture.md
    ├── 12_tech_stack.md
    ├── 13_decision_operating_system.md
    ├── 14_instantiation_guide.md
    ├── 15_implementation_roadmap.md
    ├── 16_verification_report.md
    └── business_skeleton.md
```

---

## 7. Change log

| Date | By (model) | Change |
|---|---|---|
| 2026-06-30 | Opus 4.8 | Created full v1.0 architecture package (19 artifacts) in `architecture/`. JSON + YAML validated. |
| 2026-06-30 | Opus 4.8 | Created this PROJECT.md tracker. |
| 2026-06-30 | Opus 4.8 | Initialized git repo, added README + .gitignore, pushed to GitHub (oilyrags/autonomous-business-skeleton, main). |
| 2026-06-30 | Opus 4.8 | Rewrote commit email to cliveadams@gmail.com; force-pushed. |
| 2026-06-30 | Opus 4.8 | Expanded agent registry to full roster (v2.0, 72 agents / 16 contexts); recorded thin-artifact assessment. |

---

## How to maintain this file (instructions for any model/session)

1. **On pickup:** read this file top-to-bottom, then the master spec, then any artifact relevant to the task.
2. **On any meaningful change:** update §3 (status), §4 (pending), and append a row to §7 (change log). Update "Last updated" + "Updated by" at the top.
3. **On a new locked decision:** add a row to §2.
4. **Keep it terse and current** — this is a living index, not a narrative. If it disagrees with reality, fix it immediately.
