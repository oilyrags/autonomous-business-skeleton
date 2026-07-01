# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase. **Layout: multi-context.**

## Before exploring, read these

- **`CONTEXT-MAP.md`** at the repo root — the entry point: the list of bounded contexts, the shared language that spans them, and the key integration flows.
- **`src/<context>/CONTEXT.md`** — the tight, opinionated glossary local to the context you're working in. Infer which context the topic relates to from the map; if unclear, ask.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates and extends them lazily when terms or decisions actually get resolved.

## File structure (multi-context)

```
/
├── CONTEXT-MAP.md              ← entry point: context list + shared language + relationships
├── src/
│   ├── ab_ledger/CONTEXT.md    ← one tight glossary per bounded context
│   ├── ab_social/CONTEXT.md
│   └── … (one per src/ab_* context)
├── docs/adr/                   ← architecture decision records (system-wide)
└── architecture/              ← the full v1.0 design package (deep reference)
```

Migrated from single-context (a root `CONTEXT.md`) once real code modules appeared under `src/<context>/` — one per bounded context, mapped by `CONTEXT-MAP.md`.

## Use the glossary's vocabulary

When your output names a domain concept (issue title, refactor proposal, hypothesis, test name), use the term as defined in the owning context's `CONTEXT.md` (or the shared-language section of `CONTEXT-MAP.md`). Don't drift to synonyms the glossary explicitly avoids. The authoritative long-form glossary is `architecture/02_ubiquitous_glossary.md`; the per-context `CONTEXT.md` files are its tightened, opinionated form for day-to-day agent use.

If the concept you need isn't in any glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`, and add it to the owning context's `CONTEXT.md`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 — but worth reopening because…_
