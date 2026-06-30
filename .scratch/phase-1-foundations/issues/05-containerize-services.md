# 05 — Containerize the five services

Status: done

## What to build

Replace the `sleep infinity` placeholders in docker-compose with real container
images for the five services, so the stack runs them as separate processes over
HTTP (the deployment shape the architecture assumes), not just in-process via
TestClient. A single Dockerfile builds the project; each service runs its FastAPI
app under uvicorn. Services talk to each other and to infra by container name
(in-container env overrides the localhost defaults).

- `identity`, `gateway`, `killswitch`, `audit` → uvicorn HTTP services with `/health`.
- `agent` → a small service exposing `POST /act` that mints a token and drives the
  gateway over HTTP (proving the chain end-to-end across containers).
- `audit` also runs the `AgentDecisionMade` consumer as a background loop.

## Acceptance criteria

- [ ] `docker compose up -d --build --wait` brings all 5 services + infra to healthy.
- [ ] Hitting the agent's `/act` (over its published port) returns the gateway's 200
      and persists a Decision; the audit read API shows the allow record.
- [ ] In-container env wires Postgres/OPA/Redpanda by service name; the JWT secret is
      shared so identity-minted tokens validate at the gateway.
- [ ] Existing in-process test suite still passes unchanged (`make check`).

## Blocked by

- 01 — Happy-path tracer (and 02–04 for the full flow)

## Comments

**Done (2026-06-30).** Single `Dockerfile` (uv, deps-only, `src` on PYTHONPATH) builds one shared image; each compose service overrides the command to run its uvicorn app. `make up` builds + brings all 5 services + infra to healthy (per-service `/health` checks). In-container env wires Postgres/OPA/Redpanda by service name; shared `AB_JWT_SECRET` so identity-minted tokens validate at the gateway. New `ab_agent.app` exposes `POST /act` (mints token, calls gateway over HTTP). `audit` runs the `AgentDecisionMade` consumer as a background thread (`AB_AUDIT_CONSUMER=1`).

Verified with `make smoke`: agent `/act` → gateway 200 → Decision persisted → audit allow record (seq 1) → background consumer recorded receipt (seq 2, hash-chained) → `/audit/verify` intact. In-process suite unchanged (11 green). `.dockerignore` keeps the build context small. CI still runs the in-process suite against infra only (image build not added to CI — optional follow-up).
