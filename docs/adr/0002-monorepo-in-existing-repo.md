# Code lives in the existing design repo (monorepo)

Implementation code lives under `src/` in **this** repository, alongside `architecture/` and `docs/`, as a monorepo — so the spec, ADRs, and code share one history and evolve together.

## Considered Options

- **Monorepo in this repo** (chosen) — tightest spec→code traceability; one history; the domain docs already anticipate `src/<context>/` as modules appear.
- **Separate implementation repo** — cleaner separation, but loosens traceability and requires cross-repo syncing.

## Consequences

The repo is now both the design package and the codebase. `src/` holds the walking-skeleton services as Python packages; `architecture/` and `docs/` remain the reference. When real code modules accrue under `src/<context>/`, the domain docs migrate from single-context (`CONTEXT.md`) to multi-context (`CONTEXT-MAP.md`).
