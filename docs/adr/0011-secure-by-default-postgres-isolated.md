---
status: accepted
---

# Secure-by-default: mTLS is the default DB path; Postgres is network-isolated

Supersedes the ADR-0010 caveat. The default containerized stack (`make up`) now runs the
full SPIFFE mTLS mesh, and **Postgres is reachable only via its mTLS proxy** — there is no
plaintext-direct path from the app services.

## Decision

- Postgres lives on an isolated `pgnet` network; only `postgres-proxy` bridges `pgnet` to
  the app network. App services have **no** direct route to `postgres:5432`.
- All app DB clients (gateway, audit, killswitch, identity) reach Postgres through their own
  mTLS client sidecars (per-service SPIFFE identity). `identity` gained a sidecar + identity
  (uid 1007) to complete the set.
- `make up` orchestrates the secure bring-up: infra → SPIRE bootstrap → mTLS proxies →
  services (repointed via `docker-compose.spiffe.yml`). SPIRE + proxies are no longer opt-in
  for the containerized stack.
- The host-run in-process test suite is unaffected: it uses `make up-infra` (plaintext infra
  on the host-published ports) and connects to Postgres via the published `55432` port, which
  works regardless of the internal network.

## Gotchas solved

- **SPIRE join-token single-use.** The multi-step bring-up recreated the agent, which reused
  its consumed join token and crashed. Fixed with a consistent compose invocation across all
  `make up` steps (`AB_DC`) plus `--no-recreate` so the running agent is never touched.
- Bare `docker compose up` is no longer supported (Postgres is off the app network); `make up`
  is the entry point.

## Verified (scripts/spire-secure-verify.sh; CI `docker` job)

`make up` brings all services healthy over the mesh; `agent /act`, the audit read, and the
killswitch write all go over mTLS; **the gateway cannot open a direct TCP connection to
`postgres:5432`** (negative test); and the host test suite (`make check`) stays green.

## Still deferred

gateway→Redpanda mTLS (Kafka advertised-listeners); production SPIRE node attestation
(join-token is dev-only); Postgres-native TLS is intentionally not used (ghostunnel + network
isolation gives mTLS-only without Postgres cert-auth complexity).
