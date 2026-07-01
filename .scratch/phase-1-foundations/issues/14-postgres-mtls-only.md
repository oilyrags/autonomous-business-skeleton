# 14 — Postgres mTLS-only (secure-by-default, network-isolated)

Status: done

## What to build

Make Postgres reachable only over mTLS. Chosen approach: mTLS becomes the default DB path —
Postgres is network-isolated (reachable only via its proxy) and `make up` runs the full mesh.

## Acceptance criteria

- [x] Postgres on an isolated network; app services have no direct route (verified: gateway
      cannot connect to postgres:5432 directly).
- [x] All app DB clients (gateway, audit, killswitch, identity) reach Postgres via mTLS sidecars.
- [x] `make up` = secure-by-default (infra → SPIRE → proxies → services). Host test suite
      (`make check`) still green via the published port.
- [x] CI `docker` job runs `make up` + verifies; teardown via `make down`.

## Comments

**Done (2026-07-01).** ADR-0011. Postgres moved to an isolated `pgnet` (only postgres-proxy
bridges); `identity` gained a DB sidecar + SPIFFE identity (uid 1007) to complete the set;
overlay repoints all DB clients. `make up` orchestrates the secure bring-up; `make down`
tears the mesh down. Solved the SPIRE join-token single-use crash on the multi-step bring-up
(consistent compose invocation via `AB_DC` + `--no-recreate`). Verified: all services healthy
over the mesh, `/act` + audit read + killswitch write over mTLS, **gateway cannot reach
postgres:5432 directly**, and `make check` (11 tests) green. Bare `docker compose up` is no
longer supported — `make up` is the entry point.

**Still deferred:** gateway→Redpanda mTLS; production SPIRE node attestation.

## Blocked by

- 13 — Route all app DB clients through mTLS sidecars
