# PROJECT — Autonomous AI-First Business Skeleton

> **Purpose of this file:** single source of truth for project state. Read this first if you are a new model/session picking up the work. It captures what we're building, what's decided, what's done, what's pending, and the conventions to follow — so context survives model switches. **Keep it updated as work progresses** (see "How to maintain" at the bottom).

- **Last updated:** 2026-07-01 (exfiltration egress guard, Audit 6 closed — slice 25)
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
| Development method | **Adopted Matt Pocock's spec-driven skills** (grill → PRD → issues → triage → TDD) | 2026-06-30 | 17 skills vendored to `.claude/skills/`. Config: GitHub Issues tracker, AGENTS.md, default triage labels, single-context. |

---

## 3. Status overview

**Phase: Implementation — Phase 1 Foundations, spec stage.** Architecture design package is COMPLETE (v1.0). Phase 1 has been grilled (spec-driven) into a PRD + 3 ADRs; **no code written yet** — next is `/to-issues` then `/tdd`.

**Phase 1 walking skeleton — locked decisions (grilling, 2026-06-30):** thinnest end-to-end slice = one agent identity → model gateway → OPA-authorized + audit-logged `decision_registry.write` tool call → emits `AgentDecisionMade` on Redpanda → killable within SLA. Python monorepo (`src/`); 5 services (identity, gateway, killswitch, audit, agent) + shared schema lib; OPA sidecar (default-deny), Redpanda single node, Postgres hash-chain audit; interim custom JWT issuer (Keycloak/SPIFFE deferred); real gateway + stub model; uv/ruff/mypy/pytest, docker-compose + Makefile, GitHub Actions. Spec: [`docs/prd/0001-phase-1-foundations-walking-skeleton.md`](docs/prd/0001-phase-1-foundations-walking-skeleton.md). Decisions: [ADR-0001](docs/adr/0001-python-implementation-language.md), [ADR-0002](docs/adr/0002-monorepo-in-existing-repo.md), [ADR-0003](docs/adr/0003-interim-jwt-issuer-defer-keycloak.md).

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

**Verification result (from `16`):** Accepted as buildable Mode-B design. **0 open design gaps.** Originally 5 CONDITIONAL; **Audit 9 (AI, slice 23)** and **Audit 6 (security, slice 25)** now PASS (build-proven), leaving **3 of 12 audits CONDITIONAL** — they require build-time proof (running code), not design changes:
- Audit 4 (compliance lawful-basis): CI check that personal data has an `08` entry.
- ~~Audit 6 (security): kill-switch drill within SLA; prompt-injection/exfiltration tests.~~ **CLOSED — PASS (slices 04+24+25, ADR-0021/0022): kill-switch + prompt-injection + exfiltration all build-proven.**
- Audit 7 (finance): ledger-balance invariant; double-payment failure-injection; maker-checker.
- ~~Audit 9 (AI): eval gate blocks a bad model; grounding threshold; bias evals for Art.22.~~ **CLOSED — PASS (slices 21+23, ADR-0018/0020): all three build-time criteria proven; `make eval` in CI.**
- Audit 12 (failure-injection): run the scenario suite, remediate findings.

---

## 4. What needs to be done (pending / next steps)

### Open follow-ups on the design (optional, not blocking)
- [x] **Expand `05_agent_registry.json`** to the full agent roster across all 16 bounded contexts. — *done 2026-06-30, registry v2.0, 72 agents, validated.*
- [ ] **Thin-artifact assessment (2026-06-30):** package meets all acceptance minimums. Two intentionally-representative (not exhaustive) spots remain, both noted in-file and deferrable until build:
  - `events.asyncapi.yaml` — full message schemas for ~9 of ~70 events (rest indexed in `04_event_catalog.md`). Expand all 70 on request.
  - `15_implementation_roadmap.md` — 6 representative backlog stories rather than full per-phase backlog. This is implementation-prep (overlaps the "Phase 1 build plan" option); expand when build starts.
- [ ] Consider rendering `01_context_map.mermaid` to an image for stakeholders.

### Phase 1 — Foundations (in progress, spec-driven flow)
- [x] **Grill** Phase 1 → resolved 12 decisions (walking skeleton). *(2026-06-30)*
- [x] **PRD** drafted → `docs/prd/0001-...md`; 3 ADRs written. *(2026-06-30)*
- [x] **`/to-issues`** — sliced into 5 vertical slices in `.scratch/phase-1-foundations/issues/` (local tracker fallback; mirror to GitHub Issues once `gh` is set up). *(2026-06-30)*
- [x] **Slice 00 — scaffold** (`/tdd`): Python monorepo, uv, ruff/mypy/pytest, docker-compose stack (verified healthy), CI, `ab_schemas` models + passing test. *(2026-06-30)*
- [x] **Slice 01 — happy-path tracer**: identity (JWT) + gateway (`/tool-call`) + OPA allow + `decision_registry.write` + hash-chained audit + `AgentDecisionMade` + consumer. *(2026-06-30)*
- [x] **Slice 02 — unauthorized denied**: OPA default-deny for wrong tool / wrong principal, audited, no side effect. *(2026-06-30)*
- [x] **Slice 03 — token revocation**: `revoked_principals` + `/revoke`; gateway denies revoked principal immediately. *(2026-06-30)*
- [x] **Slice 04 — kill-switch drill**: real `ab_killswitch` (global/agent flags + revoke + `KillSwitchActivated`); gateway fail-closed; halts within 2s SLA; audit-tamper breaks `verify_chain`. *(2026-06-30)*
- ✅ **Phase 1 walking skeleton COMPLETE** — 11 tests green (ruff + mypy strict + pytest), all against the live OPA/Redpanda/Postgres stack; CI runs the integration suite.

### After Phase 1 (choose next)
- [x] **Containerize the 5 services** (slice 05): one Dockerfile, uvicorn per service in compose, `/health` checks, `make up`/`make smoke`. Verified end-to-end across containers. *(2026-06-30)*
- [x] **Docker build + containerized smoke in CI** (new `docker` job: build all images, `up --build --wait`, assert agent→gateway 200 + allow audit + chain intact). Verified locally. *(2026-06-30)*
- [x] **Real OIDC IdP (Keycloak)** (slice 06): RS256/JWKS validation, client-credentials, declarative realm; supersedes ADR-0003 (→ ADR-0004). Verified live (11 tests + smoke). *(2026-06-30)*
- [x] **OIDC hardening** (slice 07, ADR-0005): gateway verifies `iss` + `aud` (Keycloak hostname pinned, audience mapper); **Vault** (dev) holds client secrets, agent + tests fetch from Vault. Verified live. *(2026-06-30)*
- [x] **SPIFFE/mTLS tracer** (slice 08, ADR-0006): SPIRE (opt-in `spiffe` profile) issues workload SVIDs (unix attestor by UID); verified SVID issuance + agent↔gateway mTLS handshake (`make spire-up && make spire-verify`; CI `spiffe` job). *(2026-07-01)*
- [x] **agent→gateway mTLS enforced** (slice 09, ADR-0007): ghostunnel sidecars fetch SVIDs from SPIRE, enforce SPIFFE-ID authz; live `/health` + full `/act` business call route over mTLS; no-SVID client rejected. Opt-in (`spiffe` profile + `docker-compose.spiffe.yml`); CI `docker` job verifies. *(2026-07-01)*
- [x] **SVID rotation drill** (slice 10): short-TTL (60s) SVIDs auto-rotate; agent→gateway mTLS serves with zero downtime across a rotation (serial changed, 40/40 requests ok). `make spire-rotation-drill`. *(2026-07-01)*
- [x] **gateway→OPA over mTLS** (slice 11, ADR-0008): ghostunnel opa-proxy/gateway-opa-proxy + `opa` SVID; `/act` authorizes via the mTLS'd OPA hop (200); no-SVID rejected. CI verifies both hops. *(2026-07-01)*
- [x] **gateway→Postgres over mTLS** (slice 12, ADR-0009): postgres-proxy/gateway-pg-proxy + `postgres` SVID; TCP tunnel of the Postgres wire; gateway startup + `/act` persist over mTLS; no-SVID rejected. `init_db` retry. CI verifies all three hops. *(2026-07-01)*
- [x] **All app DB clients over mTLS** (slice 13, ADR-0010): `audit`/`killswitch` get client sidecars + SPIFFE identities; each service reads/writes Postgres over mTLS; no-SVID rejected. CI verifies. *(2026-07-01)*
- [x] **Postgres mTLS-only / secure-by-default** (slice 14, ADR-0011): `make up` now runs the full mTLS mesh; Postgres network-isolated (gateway can't reach it directly); identity got a DB sidecar (uid 1007). Host tests green via published port. *(2026-07-01)*
- [x] **Phase 2 Core-data tracer** (slice 15, ADR-0012): `ab_data` — AgentDecisionMade → bronze Parquet → dbt-duckdb medallion → gold → code-defined metrics registry (one canonical definition per KPI) + inventory classification + quality. Batch CLI `make data`. 5 infra-free tests + live. *(2026-07-01)*
- [x] **Data service — long-running semantic layer** (slice 16, ADR-0013): `ab_data.app` (FastAPI, own `Dockerfile.data` image, in `make up`) runs a background consumer that lands bronze + rebuilds the medallion, and serves canonical KPIs over HTTP (`GET /metrics`, `GET /metrics/{name}`; unknown→404). Bronze is now **append-only Parquet parts** so the service accumulates over time. New `data` dep group keeps app images lean. 4 more infra-free tests (`test_app.py`, 9 total); live `make data-verify` (drove decisions → consumed off bus → served KPIs); CI docker job runs data-verify. *(2026-07-01)*
- [x] **Warehouse freshness SLA** (slice 17, ADR-0014): `ab_data.freshness` reads row count + newest event/ingest times from silver; pure `staleness()` → age + `within_sla` verdict (SLA via `AB_FRESHNESS_SLA_SECONDS`, default 300s). `GET /freshness` on the data service; `/health` stays pure liveness (no flap). Fixed a latent ingest tz bug — timestamps now normalized to **UTC-naive** so the warehouse is UTC regardless of host tz. +5 infra-free tests (`test_freshness.py`, 14 data tests total); data-verify asserts freshness-within-SLA after ingest. Verified live (before build → `within_sla:false`; after 3 events → 3 rows, UTC times, age ~4s, within SLA). *(2026-07-01)*
- [x] **Grain-aware KPIs + readiness gate** (slice 18, ADR-0015): new dbt model `gold_decisions_by_day` (UTC day → count) + reconciliation quality check; new canonical KPI `active_decision_days_total` (grain `daily`); `GET /series/decisions_by_day` serves the grain-aware breakdown; `GET /ready` (pure `freshness.readiness()`) → 200 only if built AND within SLA, else 503 (distinct from `/health` liveness). Registry scalar-per-KPI contract kept (series is separate). +6 infra-free tests (20 data total). Verified live: 3 decisions over 2 UTC days → `/ready` 503→200, `active_decision_days_total`=2, series `[{06-29:2},{06-30:1}]`. *(2026-07-01)*
- [x] **Bus over mTLS** (slice 19, ADR-0016): gateway (produce) + audit/data/killswitch (consume) ↔ Redpanda over SPIFFE mTLS. Solved Kafka's **advertised-listener redirect** (a naive TCP tunnel breaks — the broker advertises its own address and the client redials direct) with a dedicated Redpanda `mtls` listener (`:29093`) advertised as the client proxy `kafka-mtls:29092`. `redpanda-proxy` (server, `redpanda` SVID uid 1008) + shared `kafka-mtls` (client, `kafka-client` SVID uid 1009); 4 bus clients set `AB_KAFKA=kafka-mtls:29092`. Shared client identity (per-client would need one advertised listener each — deferred). Verified live `make spire-bus-verify` (produce+consume over mTLS; no-SVID rejected); no regression on other hops; CI runs it. *(2026-07-01)*
- [x] **Redpanda network isolation** (slice 20, ADR-0017): Redpanda moved to an isolated `busnet` (only redpanda + redpanda-proxy attach); app services have no direct route — `redpanda` doesn't even resolve for them. redpanda-proxy bridges default↔busnet as the sole path in. Host keeps `localhost:19092` (published; in-process tests unaffected). Verified live: bus produce/consume over mTLS still works, gateway CANNOT reach redpanda:9092 or :29093 directly, no regression. **Both datastores (Postgres + Redpanda) now isolated; every service hop is mTLS.** *(2026-07-01)*
- [ ] Bus hardening remainder: per-client bus SVIDs (would need per-listener advertised addrs); drop host-published plaintext listeners in a prod profile; production SPIRE node attestation (join-token is dev-only).
- [x] **Model eval + promotion gate** (slice 21, ADR-0018) — **Phase 3 (agent platform) STARTED**: `ab_evals` code-defined eval harness (per-profile `EvalSet` of deterministic cases w/ capability/safety dimensions + `critical` flag); `gate()` blocks on any critical failure or score<threshold, emitting canonical `ModelPromoted`/`ModelEvaluationFailed` (added to `ab_schemas`). `model_gateway` now serves a profile only if its model passed the gate (PromotionRegistry seeded at import); un-gated profile → deterministic fallback, never a silent guess. `make eval` = CI release gate (blocks a prompt-injection leaker + a low-capability model; self-checks the gate has teeth). +6 infra-free tests. **Closes the first of Audit 9's three build-time criteria** (`architecture/16`). *(2026-07-01)*
- [x] **Portkey model provider** (slice 22, ADR-0019): model gateway can now select & use real models via **Portkey** (portkey.ai AI-gateway, OpenAI-compatible; cloud or self-hosted OSS). `ab_gateway/providers.py` (`PortkeyModel` impl of `Model`, lazy `portkey-ai` import, injectable client) + `model_routes.py` (task-profile → Portkey config/model/virtual-key, all env-overridable). `select_model()` picks by `AB_MODEL_PROVIDER` (default `stub` → offline/CI unchanged). A Portkey model **must still pass the eval gate** to serve (selecting it never bypasses governance; un-gated → abstain, never called). Optional `models` dep group. +6 infra-free tests (injected fake client, no network); OSS gateway image confirmed to boot. *(2026-07-01)*
- [x] **Exfiltration egress guard — Audit 6 CLOSED** (slice 25, ADR-0022): `ToolSpec` gains `egress` + `clearance` (`DataClassification`); `ToolCallRequest.data_classification`; `/tool-call` refuses an **egress** tool that would transmit data above its clearance (`personal`/`financial` can't leave via a tool cleared for `internal`), audited, fail-closed. Demo `notify.external` egress tool → `outbox` table (OPA-authorized). `ToolSpec.emits_decision` gates `AgentDecisionMade` emission (egress sends don't inflate KPIs); `/tools` shows egress+clearance. +4 tests; gateway suite 29 green. **Audit 6 → PASS (build-proven)**: kill-switch (04) + injection (24) + exfiltration (25). CONDITIONAL 4→3. *(2026-07-01)*
- [x] **Tool registry + untrusted-input gate** (slice 24, ADR-0021): `ab_gateway/tools.py` → `REGISTRY` of `ToolSpec` contracts (`side_effect`, `sensitive`, description) instead of a bare name→handler dict. `ToolCallRequest.untrusted_input` (default False); `/tool-call` refuses a **sensitive** tool when `untrusted_input=true` even if OPA allowed it — prompt-injection fail-closed (architecture/10), audited, tool never runs. `GET /tools` discovery endpoint. +5 infra-free + 2 integration tests; full gateway suite (24) still green. **Contributes to Audit 6** (prompt-injection control now build-proven; injection/exfiltration suites remain). *(2026-07-01)*
- [x] **Grounding + bias eval gates — Audit 9 CLOSED** (slice 23, ADR-0020): per-dimension `thresholds` on `EvalSet` (grounding gate = a `grounding` dimension @ 1.0); `FairnessCase` paired/metamorphic bias eval (decision invariant across protected-attribute groups); gate **requires** a bias eval for `art22_significant` profiles. New `significant_customer_decision` Art.22 profile (grounding + fairness). Reference models: CompliantModel→promoted, HallucinatingModel→blocked (grounding), BiasedModel→blocked (bias). `make eval` demonstrates all three Audit-9 criteria. +5 infra-free tests. **`architecture/16` Audit 9 → PASS (build-proven); CONDITIONAL count 5→4.** *(2026-07-01)*
- [ ] Production Keycloak/Vault modes.
- [ ] Real model providers behind the gateway (vLLM / managed), replacing the stub.
- [ ] Phase 2 continue — Cube/dbt-MetricFlow server; time-windowed/grain-aware KPIs; freshness SLAs; Iceberg + Trino + OpenMetadata; more KPIs & dbt tests.
- [ ] Mirror `.scratch/phase-1-foundations/` issues to GitHub Issues once `gh` is installed.

### Run it
`make up` (secure-by-default mesh), `make smoke` (drive agent→gateway→audit end-to-end), `make spire-bus-verify` (gateway/audit/data ↔ Redpanda over mTLS), `make data-verify` (data service serves canonical KPIs + freshness from live bus events), `make eval` (model promotion gate — blocks a model that fails its eval set), `make check` (lint+types+tests; needs `make up-infra`), `make down`. **Models:** default is the offline deterministic stub; to use real models set `AB_MODEL_PROVIDER=portkey` + `uv sync --group models` + Portkey config (cloud `AB_PORTKEY_API_KEY` or self-hosted `AB_PORTKEY_BASE_URL=http://host:8787/v1`), per-profile route via `AB_PORTKEY_CONFIG_<PROFILE>`/`_MODEL_<PROFILE>`/`_VK_<PROFILE>` (see ADR-0019). A Portkey model must still pass the eval gate to serve. Service ports: gateway 18080, audit 18081, identity 18001, killswitch 18002, agent 18090, data 18085 (`/metrics`, `/metrics/{name}`, `/series/decisions_by_day`, `/freshness`, `/ready`, `/health`). Batch pipeline: `make data`.

**Local infra ports (avoid clashes):** Postgres **55432**, Redpanda **19092** (external), OPA **8181**. `make up` / `make check` / `make down`.
- [ ] **Install `gh`** + `gh auth login` + create triage labels (`gh label create …`) to enable the GitHub Issues workflow.

### Later phases (follows `15_implementation_roadmap.md`)
- [ ] Full identity (Keycloak/Zitadel + SPIFFE/mTLS — supersedes ADR-0003), Vault, GitOps, real model providers.
- [ ] **Phase 2 — Core data:** canonical model, data inventory, Iceberg lakehouse, dbt, Cube semantic layer, catalog/lineage, classification-at-ingestion.
- [ ] **Phase 3 — Agent platform:** model gateway, tool registry, agent identity, memory, eval harness + Langfuse, OTel tracing.
- [ ] **Phase 4 — Product factory** → **5 CRM/Sales/Support** → **6 Finance & compliance** → **7 C-suite & Decision OS** → **8 Portfolio operation** → **9 Continuous optimization.**
- [ ] **Close the remaining 3 CONDITIONAL audits** (4 compliance-CI, 7 finance, 12 failure-injection) with the build-time proofs listed in section 3 above. *(Audit 9 AI closed slice 23; Audit 6 security closed slice 25.)*

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
├── AGENTS.md                                           ← agent instructions + skills config
├── CONTEXT.md                                          ← tight shared-language glossary
├── README.md                                           ← GitHub landing page
├── autonomous-business-architecture-merged-prompt.md   ← the master spec (requirements)
├── .claude/skills/                                     ← 17 vendored Matt Pocock spec-driven skills
├── docs/
│   ├── agents/                                         ← skills config (issue-tracker, triage-labels, domain)
│   └── adr/                                            ← architecture decision records (created lazily)
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
| 2026-06-30 | Opus 4.8 | Adopted Matt Pocock spec-driven skills: vendored 17 skills to `.claude/skills/`, ran setup (GitHub Issues / AGENTS.md / default labels / single-context), seeded `CONTEXT.md`, wrote `docs/agents/*` + `AGENTS.md`. |
| 2026-06-30 | Opus 4.8 | Grilled Phase 1 (12 decisions) → walking-skeleton PRD (`docs/prd/0001`), ADR-0001/0002/0003, added `Walking Skeleton` to `CONTEXT.md`. No code yet. |
| 2026-06-30 | Opus 4.8 | `/to-issues`: 5 slices in `.scratch/phase-1-foundations/`. Slice 00 scaffold shipped: `src/` monorepo (uv/ruff/mypy/pytest), docker-compose stack verified healthy, CI, `ab_schemas` models + green test. First running code. |
| 2026-06-30 | Opus 4.8 | Slice 01 shipped: identity/gateway/audit + decision_registry.write + OPA allow + AgentDecisionMade + consumer. End-to-end tracer verified live (ruff+mypy+3 tests). Fixed local port clashes (Postgres 55432, Redpanda dual-listener 19092). CI runs integration tests. |
| 2026-06-30 | Opus 4.8 | Slices 02–04 shipped: OPA deny path, token revocation, real kill switch (fail-closed, SLA, KillSwitchActivated, audit-tamper). **Phase 1 walking skeleton complete** — 11 tests green against live stack. |
| 2026-06-30 | Opus 4.8 | Slice 05: containerized all 5 services (Dockerfile + uvicorn in compose, /health, agent POST /act, audit background consumer). `make up`/`make smoke` verify the chain end-to-end across containers. |
| 2026-06-30 | Opus 4.8 | Added CI `docker` job (build + containerized smoke). |
| 2026-06-30 | Opus 4.8 | Slice 06: real OIDC identity via Keycloak (RS256/JWKS, client-credentials, declarative realm). Supersedes ADR-0003 → ADR-0004; identity service → revocation only. 11 tests + smoke green with real tokens; CI waits for the realm. |
| 2026-06-30 | Opus 4.8 | Slice 07 (ADR-0005): OIDC hardening — gateway verifies iss/aud (KC hostname pinned + audience mapper); Vault (dev) holds client secrets, agent+tests fetch from Vault. 11 tests + smoke green; CI seeds Vault. SPIFFE/mTLS still open. |
| 2026-07-01 | Opus 4.8 | Slice 08 (ADR-0006): SPIFFE/mTLS tracer — SPIRE (spiffe profile) issues workload SVIDs via unix attestor by UID; verified SVID issuance + agent↔gateway mTLS handshake; CI `spiffe` job. App-integration (SVIDs into live calls) deferred; services still use plain HTTP. |
| 2026-07-01 | Opus 4.8 | Slice 09 (ADR-0007): agent→gateway mTLS enforced via ghostunnel sidecars (SVIDs from SPIRE, SPIFFE-ID authz). Live `/health` + full `/act` over mTLS; no-SVID rejected. Solved shared-PID-namespace attestation + ghostunnel unsafe flags. CI `docker` job verifies. |
| 2026-07-01 | Opus 4.8 | Slice 10: SVID rotation drill — 60s-TTL SVIDs auto-rotate; agent→gateway mTLS zero downtime across rotation (serial changed, 40/40 ok). `make spire-rotation-drill`; runnable drill (not CI). |
| 2026-07-01 | Opus 4.8 | Slice 11 (ADR-0008): gateway→OPA over mTLS (opa-proxy/gateway-opa-proxy + `opa` SVID, reusing the sidecar pattern). `/act` authorizes via mTLS'd OPA (200); no-SVID rejected. CI `docker` job verifies both hops. |
| 2026-07-01 | Opus 4.8 | Slice 12 (ADR-0009): gateway→Postgres over mTLS (postgres-proxy/gateway-pg-proxy + `postgres` SVID; TCP tunnel of the PG wire; DSN sslmode=disable; init_db retry). Gateway startup + `/act` persist over mTLS; no-SVID rejected. CI verifies all three hops. |
| 2026-07-01 | Opus 4.8 | Slice 13 (ADR-0010): all app DB clients over mTLS — audit (uid 1005) + killswitch (uid 1006) client sidecars + identities; postgres-proxy allows all three. Verified audit read + killswitch write + gateway persist over mTLS. CI verifies. |
| 2026-07-01 | Opus 4.8 | Slice 15 (ADR-0012): **Phase 2 Core-data tracer** — `ab_data`: AgentDecisionMade → bronze Parquet → dbt-duckdb medallion → gold → code-defined metrics registry (one-definition-per-KPI) + inventory classification + quality. 5 infra-free tests; live `make data` (KPIs from real events). DuckDB+Parquet+dbt (Cube/Iceberg deferred). |
| 2026-07-01 | Opus 4.8 | Slice 14 (ADR-0011): **secure-by-default** — `make up` runs the full mTLS mesh; Postgres network-isolated on `pgnet` (gateway can't reach it directly); identity DB sidecar (uid 1007). Solved SPIRE join-token single-use crash (--no-recreate + consistent invocation). Host tests green; CI uses `make up`/`make down`. |
| 2026-07-01 | Opus 4.8 | Slice 16 (ADR-0013): **data service** — `ab_data.app` (FastAPI, `Dockerfile.data`, in `make up` on 18085) runs a background consumer (bus → append-only bronze parts → dbt rebuild) and serves canonical KPIs over HTTP (`/metrics`, `/metrics/{name}`, unknown→404). Bronze switched to append-only glob (silver still dedups by event_id). New `data` dep group keeps app images lean. +4 infra-free tests (9 total). Verified live: produced decisions 3→5, `decisions_recorded_total` 3→5 / `deciding_agents_total` 2→3. `make data-verify` + CI docker step. Fixed pre-existing `__main__.py` format drift. |
| 2026-07-01 | Opus 4.8 | Slice 17 (ADR-0014): **freshness SLA** — `ab_data.freshness` (row count + newest event/ingest time from silver; pure `staleness()` → age + `within_sla`, SLA via `AB_FRESHNESS_SLA_SECONDS`=300). `GET /freshness` on the data service; `/health` stays liveness-only (no healthcheck flap). Fixed a latent ingest tz bug: tz-aware datetimes bound into DuckDB `TIMESTAMP` were shifted to host-local time (13:00Z → 15:00 on UTC+2); `_utc_naive` now stores UTC. +5 infra-free tests (14 data total). Verified live: pre-build `within_sla:false`; post-3-events 3 rows, UTC times, age ~4s, within SLA. |
| 2026-07-01 | Opus 4.8 | Slice 18 (ADR-0015): **grain-aware KPIs + readiness** — dbt `gold_decisions_by_day` (UTC day→count) + `gold_by_day_reconciles_to_silver` check; canonical KPI `active_decision_days_total` (grain daily); `GET /series/decisions_by_day` (grain-aware breakdown); `GET /ready` (pure `readiness()`) 200 iff built + within SLA else 503, separate from `/health`. Scalar-per-KPI registry kept. +6 infra-free tests (20 data total). Verified live: 3 decisions/2 UTC days → `/ready` 503→200, `active_decision_days_total`=2, series `[{06-29:2},{06-30:1}]`, registry lists 3 KPIs. |
| 2026-07-01 | Opus 4.8 | Slice 19 (ADR-0016): **bus over mTLS** — gateway/audit/data/killswitch ↔ Redpanda over SPIFFE mTLS. Beat Kafka's advertised-listener redirect with a dedicated Redpanda `mtls` listener (`:29093`) advertised as the client-proxy address `kafka-mtls:29092`. Added `redpanda-proxy` (server, `redpanda` SVID uid 1008) + shared `kafka-mtls` (client, `kafka-client` SVID uid 1009); overlay repoints `AB_KAFKA` for the 4 bus clients; bootstrap registers 1008/1009; PROXIES + CI updated. Shared client identity (per-client → per-listener, deferred). Verified live first try: produce+consume over mTLS, no-SVID rejected, other hops unaffected. |
| 2026-07-01 | Opus 4.8 | Slice 20 (ADR-0017): **Redpanda network isolation** — moved Redpanda to an isolated `busnet` (only redpanda + redpanda-proxy attach); redpanda-proxy bridges default↔busnet as the sole path in. App services have no direct route (name doesn't resolve). Host keeps published `localhost:19092`. spire-bus-verify gains an isolation check. Verified live: bus mTLS still works, gateway cannot reach redpanda:9092/:29093 directly, host port OK, no regression. Both Postgres + Redpanda now isolated; every service hop mTLS. |
| 2026-07-01 | Opus 4.8 | Slice 21 (ADR-0018): **model eval + promotion gate** (Phase 3 start) — `ab_evals` code-defined eval harness (per-profile `EvalSet`, capability + safety dims, `critical` flag); `gate()` blocks on critical failure or score<threshold → `ModelPromoted`/`ModelEvaluationFailed` (new `ab_schemas` events). `model_gateway` serves only eval-gated models (PromotionRegistry seeded at import; un-gated → deterministic fallback). `make eval` CI release gate blocks a prompt-injection leaker + a low-capability model and self-checks the gate has teeth. +6 infra-free tests; existing `test_model_gateway` still green. Closes 1st of Audit 9's 3 criteria (updated `architecture/16`). |
| 2026-07-01 | Opus 4.8 | Slice 22 (ADR-0019): **Portkey model provider** — model gateway can select & use real models via Portkey (OpenAI-compatible AI gateway; cloud or self-hosted OSS). `ab_gateway/providers.py` (`PortkeyModel`, lazy `portkey-ai` import, injectable client) + `model_routes.py` (task-profile → Portkey config/model/VK, env-overridable). `select_model()` by `AB_MODEL_PROVIDER` (default `stub`; live path unchanged). Portkey model must pass the eval gate to serve; un-gated → abstain, never called. Optional `models` dep group + mypy override. +6 infra-free tests (fake client, no network); OSS gateway image manually confirmed to boot & route. |
| 2026-07-01 | Opus 4.8 | **Portkey live-verified** (ADR-0019 follow-up): real end-to-end confirmed — task profile → Portkey catalog slug `@…/z-ai/glm-5.2` → OpenRouter → GLM-5.2, then eval→promotion gate against the LIVE model → **PROMOTED (1.00)**. Findings: provider key must live in the saved Portkey integration (workspace `block_inline_config` refuses BYOK-from-client); reasoning models return empty content if `max_tokens` too small → routes default `max_tokens=1024` (`AB_PORTKEY_MAX_TOKENS`). Dropped an unused type-ignore (typed local so mypy is consistent w/ or w/o the optional `models` group). |
| 2026-07-01 | Opus 4.8 | Slice 25 (ADR-0022): **exfiltration egress guard — Audit 6 CLOSED** — `ToolSpec.egress`+`clearance` (DataClassification); `ToolCallRequest.data_classification`; `/tool-call` blocks an egress tool transmitting data above its clearance (fail-closed, audited). Demo `notify.external`→`outbox` (OPA-authorized). `emits_decision` gates AgentDecisionMade so egress sends don't inflate KPIs; `/tools` shows egress+clearance. +4 tests; gateway suite 29 green. Audit 6 → PASS (build-proven: kill-switch+injection+exfiltration); `architecture/16` CONDITIONAL 4→3. |
| 2026-07-01 | Opus 4.8 | Slice 24 (ADR-0021): **tool registry + untrusted-input gate** — tools carry contracts (`ToolSpec`: side_effect, sensitive); `ToolCallRequest.untrusted_input`; `/tool-call` fails a sensitive tool closed on an untrusted-input flow (prompt-injection defense, §10) even if OPA allowed it (audited, no side effect); `GET /tools` discovery. +5 infra-free + 2 integration tests; gateway suite (24) green; refactor behaviour-preserving. Contributes to Audit 6 (prompt-injection control build-proven). |
| 2026-07-01 | Opus 4.8 | Slice 23 (ADR-0020): **grounding + bias eval gates — Audit 9 CLOSED** — per-dimension `thresholds` on `EvalSet` (grounding @1.0); `FairnessCase` metamorphic bias eval (decision invariant across protected-attribute groups); gate requires a bias eval for `art22_significant` profiles. New Art.22 `significant_customer_decision` suite; reference models Compliant/Hallucinating/Biased prove promote/grounding-block/bias-block. `make eval` shows all 3 Audit-9 criteria. +5 infra-free tests; ADR-0018/0019 tests still green. `architecture/16` Audit 9 → PASS (build-proven); CONDITIONAL 5→4. |

---

## How to maintain this file (instructions for any model/session)

1. **On pickup:** read this file top-to-bottom, then the master spec, then any artifact relevant to the task.
2. **On any meaningful change:** update §3 (status), §4 (pending), and append a row to §7 (change log). Update "Last updated" + "Updated by" at the top.
3. **On a new locked decision:** add a row to §2.
4. **Keep it terse and current** — this is a living index, not a narrative. If it disagrees with reality, fix it immediately.
