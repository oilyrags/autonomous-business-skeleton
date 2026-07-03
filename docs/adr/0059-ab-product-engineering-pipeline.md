---
status: accepted
---

# `ab_product` — Product Engineering domain (autonomous initiative pipeline)

Reconciles `autonomous-initiative-pipeline.prompt.md` (an LLM that "autonomously generates and ships
production code") with the skeleton's invariants. Discovered via `/ask-matt`, designed via
`/grill-with-docs`; the stack/fit decisions were grilled against the actual code (`ab_growth`
PRD 0007, `ab_factory` Blueprint/provision, `ab_gateway` registry + `authz`/OPA per ADR-0057,
`ab_console` design system per ADR-0056 v0.3 + operator auth VULN-001, `ab_monitor` M5, `ab_mvp`
Deployer port, `architecture/14_instantiation_guide.md` stages 8–9). Plan: PRD 0008.

## Decisions (grilled)

1. **The pipeline produces a deterministic scaffold from a governed `ProductBlueprint`, not shipped
   LLM code.** The LLM fills a typed spec; a deterministic generator instantiates the service/context
   from vetted templates; a human gates launch. Upholds "LLMs reason; deterministic systems execute"
   and keeps the audit replayable — the founding invariant the prompt would otherwise break.
   (Rejected: LLM writes & ships production code. Deferred: a hybrid where the LLM authors *pure leaf
   functions* behind auto-generated property tests + review — a later evolution, never touching
   money/identity/governance/theme seams.)
2. **A new `ab_product` bounded context** owns `ProductInitiative`, `ProductBlueprint`,
   `BusinessCharter`, the gated SDLC, and the `Scaffolder`; its governed ingress is a
   `product.initiative.promote` gateway tool (tenant-bound, audited); it feeds `ab_factory` to mint
   or attach the `business_id`. Mirrors the instantiation guide's "Product" owner. (Rejected:
   overloading `ab_factory` (capital + readiness) or `ab_growth` (experimentation).)
3. **Distinct design language + forever-consistency = a versioned `BusinessCharter` + a pure
   `charter_conformance` gate.** Per-`business_id` design tokens → a deterministically-generated,
   unique daisyUI theme (CSS custom properties, vendored, no build); a machine-checkable tech charter
   (mandated stack + architecture rules + allowed deps). The `Scaffolder` generates *from* the
   charter; the gate fails any non-conformant addition (CI + launch gate). Additions bump the charter
   version (append-only) — extend, never diverge. (Rejected: per-business themes only — a color swap,
   not a design language, and no architecture/tech enforcement; docs-only conventions — drift.)
4. **Deployment target = a skeleton-native FastAPI + vendored-daisyUI service per product**, in the
   governed SPIFFE mTLS mesh, `business_id`-scoped, behind a `Deployer` port (`StubDeployer` in CI =
   render-smoke; real adapter → compose `ventures` profile now, k8s/cloud later). Reconciles the
   no-Node / vendored-Tailwind / infra-free-CI / single-governed-ingress constraints. (Rejected:
   arbitrary per-business repos/stacks — un-auditable snowflakes; static-only — too limited.)
5. **The SDLC is a deterministic gated state machine.** The LLM proposes each stage artifact through
   an injected port; deterministic gates admit it (charter conformance, tests green, DPIA trigger,
   budget cap); **humans approve the launch gate + any DPIA** (the guide's human gates 7 & 15) via
   the console; launched products auto-instrument through the `ab_monitor` M5 / `ab_console` /
   `ab_data` rails. Mirrors `ab_growth`'s propose→gate. (Rejected: fully autonomous no-gate ship;
   status-tracker-only.)
6. **Tracer bullet = promote → `ProductBlueprint` → `Scaffolder` emits one charter-conformant service
   → `charter_conformance` gate.** The full spine, minimal; the SDLC stage gates, human launch/DPIA
   gates, the `Deployer`, the console `/product` workspace, and monitoring auto-wiring are later
   slices (PRD 0008 P2–P7).

## Determinism & governance (not grilled — inherited)

- Single governed ingress: every promotion goes through `ab_gateway` (OPA default-deny + tool
  registry + untrusted-input/egress guards + hash-chained audit). The pipeline adds no new ingress.
- `business_id` is a first-class dimension on the tool, blueprint, charter, scaffold, and events.
- Ports + stubs at every external seam (LLM spec/design, the Scaffold writer, the Deployer); pure
  cores (classify, charter, conformance, pipeline) infra-free in CI.

## Consequences

- The skeleton gains, for the first time, a governed path from *validated idea* to *shipped,
  monitored, business-wired product* — the instantiation guide's stages 8–9 made real.
- A clear, auditable determinism line: the LLM proposes specs/design tokens (advisory); the
  classification, blueprint validation, scaffolder templates, theme generation, conformance, gates,
  and launch are deterministic and replayable.
- Each business becomes a distinct, self-consistent product by construction: the `BusinessCharter`
  is the single source of truth for its design language *and* its tech/architecture, enforced
  mechanically rather than by convention.
- Reuses ADR-0056 v0.3 (vendored daisyUI themes), VULN-001 (operator auth for the human gates),
  ADR-0057 (tenant binding for the tool), and the M5 monitoring rail — no new frameworks or build
  step.

## Rejected / deferred

Shipping raw LLM code; per-business repos/stacks; docs-only design conventions; a fully autonomous
no-human-gate pipeline. Deferred: LLM-authored leaf logic behind generated tests; external (k8s/
cloud) deploy adapters; the full 15-stage business-formation pipeline (reuse existing contexts);
multi-service products. Each is logged in PRD 0008 rather than silently dropped.
