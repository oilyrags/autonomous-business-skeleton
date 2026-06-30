# AGENTS.md

Agent instructions for the **Autonomous AI-First Business Skeleton** project.

## Orientation

- **Read [`PROJECT.md`](PROJECT.md) first** — it is the living source of truth (status, decisions, pending work, conventions, change log).
- Requirements spec: [`autonomous-business-architecture-merged-prompt.md`](autonomous-business-architecture-merged-prompt.md).
- The v1.0 design package lives in [`architecture/`](architecture/) (19 artifacts, Mode B).
- Shared language: [`CONTEXT.md`](CONTEXT.md) (tight glossary) ← derived from [`architecture/02_ubiquitous_glossary.md`](architecture/02_ubiquitous_glossary.md) (full glossary).

## Agent skills

This repo uses [Matt Pocock's spec-driven skills](https://github.com/mattpocock/skills), vendored under [`.claude/skills/`](.claude/skills/). Workflow: `/grill-me` or `/grill-with-docs` → `/to-prd` → `/to-issues` → `/triage` → `/tdd`, with `/diagnosing-bugs` and `/improve-codebase-architecture` as needed. `/ask-matt` routes you to the right one.

### Issue tracker

Issues and PRDs are tracked in **GitHub Issues** (repo `oilyrags/autonomous-business-skeleton`, via the `gh` CLI). External PRs are **not** a triage surface. See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See [`docs/agents/triage-labels.md`](docs/agents/triage-labels.md).

### Domain docs

**Single-context**: one root `CONTEXT.md` + `docs/adr/`. Migrates to multi-context (`CONTEXT-MAP.md`) when code modules appear under `src/<context>/`. See [`docs/agents/domain.md`](docs/agents/domain.md).

## Conventions

- Spec is law (the merged prompt). Prefer Mode B machine-readable contracts.
- DDD discipline, determinism boundary, compliance honesty, human-on-the-loop autonomy — see PROJECT.md §5.
- Keep `PROJECT.md` updated (status, pending, change log) on any meaningful change.
- Commit/push only when asked; this is a real GitHub repo on `main`.
