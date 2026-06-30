# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase. **Layout: single-context.**

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the tight, opinionated shared-language glossary.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure (single-context)

```
/
├── CONTEXT.md            ← tight shared-language glossary
├── docs/adr/             ← architecture decision records (created lazily)
└── architecture/         ← the full v1.0 design package (deep reference)
```

> **Migration note:** this project's architecture defines 16 bounded contexts (`architecture/01_context_map.mermaid`). It is treated as **single-context for the skills** while it is design/docs only. When real code modules appear under `src/<context>/`, migrate to multi-context by adding a root `CONTEXT-MAP.md` pointing at per-context `CONTEXT.md` files.

## Use the glossary's vocabulary

When your output names a domain concept (issue title, refactor proposal, hypothesis, test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids. The authoritative long-form glossary is `architecture/02_ubiquitous_glossary.md`; `CONTEXT.md` is its tightened, opinionated form for day-to-day agent use.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 — but worth reopening because…_
