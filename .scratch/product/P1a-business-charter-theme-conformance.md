# P1a — BusinessCharter + theme generation + charter conformance (design-language spine)

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
The per-business design-language + tech identity, as pure deterministic cores — the novel, riskiest
piece, landing first with zero plumbing. Each `business_id` owns a versioned **BusinessCharter**:
**design tokens** (primary/secondary/accent/neutral colours, radius scale, type scale, density) and
a **tech charter** (mandated stack = FastAPI + vendored daisyUI; architecture rules = `business_id`
tenancy, ports+stubs, single governed ingress; allowed dependency set). A deterministic
`render_theme(charter)` turns the tokens into a **unique daisyUI theme** expressed as CSS custom
properties — vendored, no build step, exactly like the console's `business`/`corporate` themes
(ADR-0056 v0.3). A pure `charter_conformance(artifact, charter)` returns a report of whether an
addition uses the charter's theme tokens, the mandated stack, and the architecture patterns, and
references the charter version. Two different businesses must yield visibly different themes; an
addition that omits the theme tokens / uses a forbidden dependency / breaks a rule must fail.

Lives in a new `ab_product` package (create its `CONTEXT.md` with the domain glossary from PRD 0008:
Business Charter, Charter Conformance, design tokens, tech charter).

## Acceptance criteria
- [ ] `BusinessCharter` is a typed, versioned, `business_id`-scoped model (design tokens + tech charter).
- [ ] `render_theme` deterministically emits a daisyUI theme (CSS custom properties); two distinct
      charters produce distinct, non-overlapping theme output (independent literals in the test).
- [ ] `charter_conformance` PASSES a conformant artifact and FAILS each of: missing theme tokens,
      forbidden dependency, violated architecture rule, missing/blank charter-version reference.
- [ ] A charter addition bumps the version (append-only) and cannot contradict prior tokens/rules.
- [ ] All pure + infra-free; `ruff` + `mypy --strict` + `pytest` green; `ab_product/CONTEXT.md` added.

## Blocked by
None — can start immediately.
