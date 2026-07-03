# P7 — Compliance (DPIA) + closing docs (PRD complete)

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
Close the loop on governance + documentation. Wire the **DPIA trigger**: an initiative that processes
personal data gates on the human DPIA approval (via `ab_compliance` RoPA / lawful-basis, matching the
instantiation guide's human gate 7) before it can reach launch; add `08` data-inventory entries for
any new personal data an initiative introduces. Finish the docs: `ab_product/CONTEXT.md` (full
glossary), `CONTEXT-MAP.md` entry + relationships, a cross-reference from
`architecture/14_instantiation_guide.md` (stages 8–9 now real), ADR-0059 shipped notes, and mark
PRD 0008 complete.

## Acceptance criteria
- [ ] A personal-data initiative is blocked from launch until the human DPIA approval is recorded
      (deterministic gate; infra-free test of the trigger logic).
- [ ] `08` inventory entries added for new personal data; compliance gate routes through `ab_compliance`.
- [ ] CONTEXT.md + CONTEXT-MAP + instantiation-guide cross-ref updated; PRD 0008 marked complete;
      `ruff` + `mypy` + `pytest` + `make check` green.

## Blocked by
- P2 (the launch gate), P3 (the human-approval surface).
