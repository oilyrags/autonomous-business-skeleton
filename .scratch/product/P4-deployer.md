# P4 — Skeleton-native Deployer (compose ventures profile)

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
Ship a scaffolded product into the governed mesh. A `Deployer` **port**: `StubDeployer` (records,
render-smoke in CI) and a real adapter that targets a compose **`ventures`** profile. The Scaffolder
(P1b) emits a `Dockerfile` + a compose fragment for the `business_id`-scoped FastAPI + vendored-
daisyUI service; deployment joins the SPIFFE mTLS mesh and publishes a `ProductDeployed` event. The
launched product is reachable behind the governed gateway and `business_id`-scoped. A real external
target (k8s/cloud) is a later adapter behind the same port (out of scope here).

## Acceptance criteria
- [ ] `Deployer` port + `StubDeployer` (records deployments; a render-smoke proves the scaffolded
      service starts + serves its themed page, like `make console`).
- [ ] The Scaffolder emits a valid `Dockerfile` + compose fragment for the product service.
- [ ] Deploying publishes `ProductDeployed` (AsyncAPI-documented); the service is `business_id`-scoped
      and behind the gateway.
- [ ] Compose config validates; `ruff` + `mypy` + `pytest` green (deploy happy path infra-gated).

## Blocked by
- P1b (a scaffold to deploy).
