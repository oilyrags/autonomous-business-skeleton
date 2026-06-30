# Vendored skills — Matt Pocock's "Skills For Real Engineers"

These 17 skills are vendored from **[mattpocock/skills](https://github.com/mattpocock/skills)** (the spec-driven engineering set listed in that repo's `.claude-plugin/plugin.json`). They give this project a disciplined, spec-driven development workflow that works with any model.

- **Source:** https://github.com/mattpocock/skills
- **License:** MIT — Copyright (c) 2026 Matt Pocock (see upstream `LICENSE`). Retained here per the MIT notice requirement.
- **Vendored:** 2026-06-30. To update, re-copy from upstream or run `npx skills@latest add mattpocock/skills`.

Project configuration for these skills lives in [`/AGENTS.md`](../../AGENTS.md) → "Agent skills", with details in [`/docs/agents/`](../../docs/agents/). Configured via the `setup-matt-pocock-skills` flow: **GitHub Issues** tracker, **default triage labels**, **single-context** domain docs (`/CONTEXT.md`).

## The workflow (typical order)

1. **`/grill-me`** or **`/grill-with-docs`** — get relentlessly interviewed to align on what to build (grill-with-docs also updates `CONTEXT.md` + ADRs).
2. **`/to-prd`** — synthesize the conversation into a PRD on the issue tracker.
3. **`/to-issues`** — break the plan/PRD into independently-grabbable vertical-slice issues.
4. **`/triage`** — move issues through the triage state machine into agent-ready or human-ready briefs.
5. **`/tdd`** — implement test-first (red-green-refactor).
6. **`/diagnosing-bugs`** — disciplined loop for hard bugs.
7. **`/improve-codebase-architecture`** — periodically rescue the design from entropy.
8. **`/ask-matt`** — router: ask which skill/flow fits your situation.

## Installed skills

**User-invoked** (only reachable when you type them): `ask-matt`, `grill-with-docs`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `to-issues`, `to-prd`, `grill-me`, `handoff`, `teach`, `writing-great-skills`.

**Model-invoked** (you or the agent can reach for them): `prototype`, `diagnosing-bugs`, `tdd`, `domain-modeling`, `codebase-design`, `grilling`.

> Note: this project keeps its own `/PROJECT.md` tracker and its v1.0 architecture package under `/architecture/`. The spec-driven skills complement those — use `CONTEXT.md` as the tight shared-language glossary (derived from `architecture/02_ubiquitous_glossary.md`) and the architecture docs as the deep reference.
