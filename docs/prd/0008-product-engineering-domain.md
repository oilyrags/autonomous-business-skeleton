# PRD 0008 — `ab_product`: Product Engineering domain (Autonomous Initiative Pipeline)

> Triage: `ready-for-agent`. Source: `autonomous-initiative-pipeline.prompt.md` (2026-07-03),
> reconciled to the skeleton via `/ask-matt` → `/grill-with-docs`. Decisions: ADR-0059 (grilled).
> Builds on `ab_growth` (PRD 0007), `ab_factory` (Blueprint/provision), the governed `ab_gateway`
> (tool registry + `authz` + OPA, ADR-0057), `ab_ledger`/`ab_audit`/`ab_data`, `ab_console`
> (design system, ADR-0056 v0.3, operator auth VULN-001), `ab_monitor` (M5), `ab_mvp` (Deployer
> port), and `architecture/14_instantiation_guide.md` (stages 8–9). Tracker: no `gh` → issues under
> `.scratch/product/`.

## Problem statement

The skeleton can *validate* an initiative (growth experiments, PRD 0007) but has no governed way to
**engineer and ship** it. The instantiation guide (architecture/14) names the Product Engineering
stages — "8. Product prototype (spec + ADRs)", "9. MVP build (code-gen + tests + CI/CD)" — but they
are unbuilt, and there is no `ab_product` context. The attached prompt proposes an LLM that
*autonomously generates and ships production code*, which collides head-on with the skeleton's
founding invariant ("LLMs reason; deterministic systems execute; every money/identity/access
decision is deterministic and audit-replayable") and its no-Node / vendored-Tailwind / infra-free-
Python-CI stance. A further hard requirement: **each business must have a distinct design language,
and every later addition must stay consistent** across architecture, tech, and design.

## Solution

A new **`ab_product`** bounded context that promotes a validated initiative through a **deterministic,
gated SDLC** and instantiates it as a **new business** (`business_id`) or an **extension** of one —
governed end to end, skeleton-native. The LLM proposes; deterministic code decides and generates:

1. A governed **`product.initiative.promote`** gateway tool (tenant-bound, audited) — the single
   ingress from growth → engineering.
2. A **`ProductBlueprint`** (a typed spec the LLM fills through a port) and a per-business
   **`BusinessCharter`** (design tokens → a unique daisyUI theme + a machine-checkable tech charter).
3. A **deterministic `Scaffolder`** that instantiates a `business_id`-scoped FastAPI + vendored-
   daisyUI product service *from vetted templates*, themed by the charter, pre-wired to the governed
   loop — never free-hand LLM code.
4. A pure **`charter_conformance`** gate every addition must pass (uses the business's theme tokens,
   the mandated stack, the architecture patterns), so a business stays consistent forever; additions
   **extend** the charter (versioned), never diverge.
5. A **gated state machine** (intake → spec → design → blueprint → scaffold → QA → launch) with
   deterministic gates and **human launch + DPIA gates** (the guide's gates 7 & 15), reusing the
   `ab_monitor` M5 / `ab_console` / `ab_data` rails for QA + observability.

"Matt-Pocock rigor" (strict typing, fast tests, clear ADRs, great DX) lives in the **templates and
the generated scaffold** — which are deterministic and reviewed — not in un-replayable model output.

## Grilled decisions (ADR-0059)

1. **The pipeline produces a deterministic scaffold from a governed `ProductBlueprint`, not shipped
   LLM code.** The LLM fills a typed spec; a deterministic generator instantiates the context/service
   from templates; a human gates launch. (Rejected: LLM writes & ships production code; hybrid
   LLM-leaf-logic — deferred as a possible later evolution.)
2. **Home = a new `ab_product` context** owning `ProductInitiative`, `ProductBlueprint`,
   `BusinessCharter`, the gated SDLC, and the `Scaffolder`; ingress is the governed
   `product.initiative.promote` tool; it feeds `ab_factory` to mint/attach the `business_id`.
   (Rejected: extend `ab_factory` / `ab_growth`.)
3. **Distinct design language + consistency = a versioned `BusinessCharter` + a pure
   `charter_conformance` gate.** Design tokens → a generated, unique daisyUI theme (CSS custom
   properties, vendored, no build); a tech charter (mandated stack + architecture rules + allowed
   deps). The Scaffolder reads the charter to generate conformant code + UI; the gate fails any
   addition that doesn't conform. (Rejected: per-business themes only; docs-only conventions.)
4. **Deployment target = a skeleton-native FastAPI + vendored-daisyUI service per product**, in the
   governed SPIFFE mTLS mesh, `business_id`-scoped, behind a **`Deployer` port** (`StubDeployer` in
   CI = render-smoke; real adapter targets the compose `ventures` profile today, k8s/cloud later).
   No Node, deterministic CI, one governed ingress. (Rejected: arbitrary repos/stacks; static-only.)
5. **The SDLC is a deterministic gated state machine.** LLM proposes each stage artifact via an
   injected port; deterministic gates admit it (charter conformance, tests green, DPIA trigger,
   budget cap); **humans approve launch + DPIA** via the console; launched products auto-instrument
   through the M5/console/data rails. (Rejected: fully autonomous no-gates; status-tracker-only.)
6. **Tracer bullet = promote → `ProductBlueprint` → `Scaffolder` emits one charter-conformant service
   → `charter_conformance` gate.** The full spine, minimal; SDLC stages, human gates, Deployer,
   console workspace, and monitoring wiring land in later slices.

## Ubiquitous language (new `ab_product` context — CONTEXT.md ships with P1)

- **Product Initiative** — a validated growth outcome promoted for engineering: `initiative_id`,
  `business_context` (existing `business_id` or null), title, hypothesis, expected impact,
  key features, constraints, priority. The unit the pipeline drives.
- **Classification** — the deterministic decision **new business** (mint a `business_id`) vs
  **extension** (attach to an existing one), with rationale. Never an LLM decision.
- **Product Blueprint** — the typed engineering spec (features, data-model shapes, screens, gateway
  tools needed, event additions) the LLM fills through a port; deterministic-validated before use.
- **Business Charter** — the versioned, per-`business_id` identity: **design tokens** (→ a unique
  daisyUI theme) + a **tech charter** (mandated stack, architecture rules, allowed deps). An
  addition **extends** the charter (a new version), never contradicts it.
- **Scaffolder** — the deterministic generator that writes a `business_id`-scoped, charter-conformant
  FastAPI + vendored-daisyUI service from vetted templates. Pure over its inputs (blueprint + charter).
- **Charter Conformance** — the pure check that an addition uses the business's theme tokens, the
  mandated stack, and the architecture patterns. Fail = no ship.
- **Stage / Gate** — a step in the SDLC (intake…launch) and the deterministic (or human) condition
  that admits it. A failed gate halts the initiative (the guide's model).
- **Launch Gate** — the human approval (with DPIA sign-off when triggered) that ships a product.

## Slices (vertical, tracer-bullet first)

**P1 — Tracer bullet (`product.initiative.promote` → scaffold → conformance).**
- `ab_schemas`: `ProductInitiative` + `ProductBlueprint` arg/spec models; `ProductScaffolded` event
  (AsyncAPI-documented).
- `ab_product/charter.py` (pure): `BusinessCharter` (tokens + tech charter) + `render_theme(charter)
  → daisyUI theme CSS` + `charter_conformance(artifact, charter) → Report`.
- `ab_product/classify.py` (pure): `classify(initiative) → NEW | EXTENSION` + rationale.
- `ab_product/scaffold.py` (pure-ish): `scaffold(blueprint, charter) → ScaffoldPlan` (the files +
  themed service) — deterministic templates; a `StubScaffoldWriter` records, a real writer emits to
  disk behind a port.
- `ab_gateway.tools.promote_initiative` handler: validate → tenant-bind (`authz`) → classify →
  build blueprint (stub spec) → conformance gate → return `initiative_id`; registered in `REGISTRY`
  (`write`, `sensitive`); OPA rule + `authz` grant for the product agent (`product.engineering_agent`).
- Tests (infra-free): tenant/authority denials, classification, theme renders unique CSS per
  business, conformance passes a conformant plan / fails a non-conformant one, scaffold plan shape.

**P2 — Gated SDLC state machine + persistence.** `ab_product/pipeline.py` pure stage/gate core
(intake→spec→design→blueprint→scaffold→QA→launch; a failed gate halts); `product_initiatives` table
+ `ab_product/store.py` (mirrors `ab_growth`); events per transition.

**P3 — Console `/product` workspace + human gates.** A daisyUI workspace (operator-authed, VULN-001):
promoted initiatives, stage/gate status, a **charter theme preview swatch**, and the **launch + DPIA
approval** through a governed `ProductPort` (stub + Http adapter, service-agent identity + operator
as maker — the E2 pattern).

**P4 — `Deployer` (skeleton-native).** `StubDeployer` (records; render-smoke CI) + a real adapter
(compose `ventures` profile); the Scaffolder emits a `Dockerfile` + compose fragment; `ProductDeployed`
event; a launched product joins the mesh, `business_id`-scoped.

**P5 — LLM spec/design adapters + demo.** Real `ModelGateway` adapters behind the `ProductModel` port
(blueprint spec, design-token proposal), degrade-safe (like `ab_growth`'s ideate); `make product` /
`./abctl product` end-to-end demo (promote → blueprint → charter → scaffold → conformance → launch-ready).

**P6 — Monitoring + KPIs.** `ab_product` Prometheus gauges (`ab_product_initiatives`, by stage;
`ab_product_launched`; `ab_product_charter_conformance`) on the console `/metrics` (M5 rail) + Grafana
panels; `ProductScaffolded`/`ProductDeployed` → `ab_data` projections.

**P7 — Compliance + docs.** DPIA trigger via `ab_compliance` (personal-data initiatives gate on the
human DPIA); `08` data-inventory entries; `CONTEXT.md` + `CONTEXT-MAP` + instantiation-guide
cross-reference; PRD marked complete.

## Determinism boundary (the audit line)

| Deterministic (replayable; may gate/ship) | Advisory (LLM; never gates/ships) |
|---|---|
| classification; `ProductBlueprint` validation; `charter_conformance`; the `Scaffolder` templates; the theme-CSS generator; stage gates; budget cap; tenant/authority binding; launch gate | blueprint spec *content*; design-token *proposals*; design/architecture narrative; stage rationale |

## Distinct design language, enforced (the headline requirement)

`BusinessCharter` (per `business_id`, versioned) holds **design tokens** — primary/secondary/accent/
neutral colors, radius scale, type scale, density — which `render_theme` turns **deterministically**
into a unique daisyUI theme (CSS custom properties; vendored, no build, exactly like the console's
`business`/`corporate` themes). The **tech charter** fixes the stack (FastAPI + vendored daisyUI +
that theme), the architecture rules (`business_id` tenancy, ports+stubs, single governed ingress),
and the allowed dependency set. Every scaffold/addition is generated *from* the charter and must pass
`charter_conformance` (theme tokens present + used; mandated stack; architecture patterns; charter
version referenced) — in CI **and** at the human launch gate. Adding to a business bumps the charter
version (append-only); it can extend the language, never contradict it. Result: each business is a
distinct, self-consistent product — by construction, not convention.

## Out of scope / follow-ups (logged, not dropped)

- **LLM-authored leaf logic** behind generated property tests (grill decision 1's hybrid) — deferred.
- **External deploy targets** (k8s/cloud) behind the `Deployer` port — the compose adapter first.
- **Full 15-stage instantiation pipeline** (market research, financial model, GTM, billing) — P2
  models the *engineering* stages (8–9); the business-formation stages reuse `ab_factory`/existing
  contexts and are wired incrementally, not rebuilt.
- **Multi-service products** (a business shipping several services) — one service per product first.

## Success criteria

A validated initiative can be promoted through the **single governed path** and become a
`business_id`-scoped, **charter-conformant** FastAPI + daisyUI product service — classified
(new/extension), spec'd (LLM-proposed, deterministically validated), scaffolded (deterministic
templates), conformance-gated, human-launched, deployed into the mesh, and monitored — with each
business carrying its **own distinct, enforced design language** and every later addition provably
consistent in architecture, tech, and design. All infra-free-testable; ruff + mypy-strict + pytest
green; the LLM never ships un-replayable code.
