# P3 — Console /product workspace + human launch/DPIA gates

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
A daisyUI **`/product` workspace** in `ab_console` (new nav entry, operator-authed per VULN-001,
in the vendored-Tailwind design system): promoted initiatives with their **stage/gate status**, a
**charter theme-swatch preview** (render the business's generated daisyUI theme so the operator sees
its distinct design language), and the **human launch + DPIA approval** dispatched through a governed
`ProductPort` (stub + Http adapter, calling under the service-agent identity with the operator as
`maker` — the E2 `GrowthPort` pattern). Mutations require a mutating role + origin check. Advisory
LLM narrative (spec/design rationale) is rendered visually distinct from deterministic gate verdicts,
as in the `/growth` workspace.

## Acceptance criteria
- [ ] `GET /product` (operator-authed) lists initiatives + stages + a charter theme-swatch preview;
      unauthenticated → 401.
- [ ] Launch/DPIA approval POSTs through the governed `ProductPort` (operator recorded as `maker`);
      read-only role → 403; cross-origin → 403.
- [ ] Pure view-models per panel; advisory narrative visually distinct from deterministic verdicts.
- [ ] Verified live in both themes (dark/light); `ruff` + `mypy` + `pytest` green.

## Blocked by
- P1b, P2.
