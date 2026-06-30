# 00 — Scaffold the walking-skeleton monorepo

Status: done

## What to build

Prefactor (done first): the runnable shell the other slices grow into. A Python monorepo under `src/` with the five service packages (identity, gateway, killswitch, audit, agent) and a shared `schemas` package, dependency/venv via uv, lint+format via ruff, types via mypy (strict), tests via pytest. A `docker-compose.yml` brings up OPA, Redpanda, and Postgres plus placeholder containers for the five services, all health-checked. A `Makefile` exposes `make up`, `make down`, `make test`, `make lint`, `make typecheck`. GitHub Actions runs lint + typecheck + tests on push/PR.

No behaviour yet beyond a single trivial passing test in the `schemas` package that proves the toolchain runs (e.g. the `AgentDecisionMade` Pydantic model round-trips an example from `events.asyncapi.yaml`).

## Acceptance criteria

- [ ] `uv sync` installs the workspace; `src/` holds 6 packages (identity, gateway, killswitch, audit, agent, schemas).
- [ ] `make up` brings the stack to healthy (OPA, Redpanda, Postgres + 5 service placeholders); `make down` tears it down.
- [ ] `make lint` (ruff), `make typecheck` (mypy strict), `make test` (pytest) all run and pass.
- [ ] `schemas` package has at least one model matching the AsyncAPI envelope + `AgentDecisionMade`, with one passing round-trip test using an independent literal example.
- [ ] GitHub Actions workflow runs lint + typecheck + tests and is green.

## Blocked by

None — can start immediately.

## Comments

**Done (2026-06-30).** All acceptance criteria met and verified locally:
- uv virtual-project workspace; `src/` holds 6 packages (ab_schemas, ab_identity, ab_gateway, ab_killswitch, ab_audit, ab_agent).
- `make up` brought the stack to **healthy** (OPA 1.18.1, Redpanda v24.2.7, Postgres 16 + 5 service placeholders); `make down` tears it down.
- `make lint` (ruff check + format), `make typecheck` (mypy strict, 8 files), `make test` (pytest) all pass — twice, stably.
- `ab_schemas.events` has `AgentDecisionMade` + `KillSwitchActivated` + envelope; round-trip test passes against an independent AsyncAPI literal.
- GitHub Actions CI workflow added (lint + typecheck + test).

Notes / deviations:
- Root is a uv **virtual project** (`tool.uv.package = false`) with `src` on path via pytest `pythonpath` + mypy `mypy_path`, instead of an editable install — the hatchling multi-package editable `.pth` was flaky across `uv run` re-syncs. Per-service distribution wheels deferred until deploy.
- OPA pinned to `1.18.1` (the `0.70.0-rootless` tag doesn't exist; OPA moved to 1.x). Default-deny `config/opa/policy.rego` in place; the allow rule lands in slice 01.

