---
status: accepted
---

# MVP/landing-page generator + deployer port

Closes the P0 "rapid MVP generation, one-click deployment" gap. A business's `Blueprint` becomes a
landing page and goes live at a URL an experiment can point traffic at. PRD 0003; spec-driven.

## Decisions

- **New `ab_mvp` context.** `render(blueprint) -> PageArtifact` is a **deterministic template** (no
  LLM) — the same blueprint always yields the same page and `content_hash` (sha256), so a redeploy is
  idempotent and diffable. The page is built from real blueprint fields (name, enabled modules,
  business_id).
- **Deployer is a port** (`Deployer.deploy(artifact) -> Deployment`) with a `StubDeployer` returning
  a stable stub URL (`https://<business_id>.mvp.stub.local/`) and no network. A real
  Vercel/Netlify/container adapter implements the same `deploy` — the generator never changes.
- **`deploy_mvp(blueprint, deployer)`** renders + deploys + returns the deployment and its
  `MvpDeployed` event (business-scoped) — added to `ab_schemas` + `events.asyncapi.yaml`; the
  ADR-0037 contract test drove the spec addition.

## Verified

3 pure tests (render is deterministic + names the business; a different blueprint yields a different
hash; `deploy_mvp` returns the URL + a business-scoped event carrying the page hash). AsyncAPI
contract green (+3). `make mvp` (in CI) deploys two blueprints to stub URLs. Full suite 191 passed,
36 skipped; ruff + mypy strict clean (93 files).

## Deferred

Real hosting adapter (Vercel/Netlify/container); richer generation (LLM-authored copy behind the
gateway, A/B page variants for `ab_growth`); wiring conversion tracking from the deployed page back
to `ab_ads` attribution.
