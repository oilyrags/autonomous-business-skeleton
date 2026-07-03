# P5 — Real LLM adapters (ProductModel) + make product demo

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
The real, degrade-safe LLM behind the `ProductModel` port: adapters over `model_gateway` (Portkey/
GLM behind the `ab_evals` gate) that propose the **blueprint spec** and the **design-token** set —
abstaining safely (no fabrication) when no eval-gated model is promoted or output is malformed
(exactly like `ab_growth.ideate.ModelGatewayIdeationModel`). Add a `make product` / `./abctl product`
demo that runs the full spine deterministically with the stub model: promote → classify → blueprint
→ charter (with proposed tokens) → scaffold → conformance → launch-ready, printing the determinism
line (LLM proposed the spec/tokens; classification, scaffold, conformance, and gate are
deterministic). Wire the demo as a CI step.

## Acceptance criteria
- [ ] `ModelGatewayProductModel` proposes blueprint spec + design tokens; abstains to empty/default
      (never fabricates) without a promoted model or on malformed output (infra-free test).
- [ ] `make product` / `./abctl product` runs end-to-end on the stub, exits 0, creates exactly the
      expected conformant scaffold; added as a CI step.
- [ ] `ruff` + `mypy` + `pytest` green.

## Blocked by
- P1b (the ProductModel port + spine). P2 ideal but not required.
