---
status: accepted
---

# Extend mTLS to the gateway→Postgres hop

Apply the ghostunnel sidecar pattern (ADR-0007/0008) to a **stateful TCP** protocol: the
gateway's Postgres connection now runs over mutual TLS, proving the template generalizes
beyond HTTP.

## Decision

- New workload identity `spiffe://ab.internal/postgres` (SPIRE, unix attestor uid 1004).
- **postgres-proxy** (ghostunnel server, uid 1004 → postgres SVID): TCP-tunnels
  `postgres:5432`, accepts only `--allow-uri spiffe://ab.internal/gateway`.
- **gateway-pg-proxy** (ghostunnel client, uid 1002 → gateway SVID): the gateway's client
  side; `--verify-uri spiffe://ab.internal/postgres`.
- Secured overlay repoints the gateway's DSN to
  `postgresql://ab:ab@gateway-pg-proxy:5432/ab?sslmode=disable` — `sslmode=disable` because
  TLS is handled by ghostunnel, not Postgres itself (Postgres stays plaintext behind its
  proxy). `init_db()` gained a connect-retry so startup tolerates the sidecar not being
  ready yet.

## Verified (scripts/spire-secure-verify.sh; CI `docker` job)

The gateway has no direct route to Postgres (DSN repointed), so the gateway becoming
**healthy** already proves its startup `init_db()` ran over mTLS. `agent /act` → 200 with
the Decision persisted confirms live writes over the mTLS'd Postgres hop; a no-SVID client
is rejected at postgres-proxy.

## Scope / still deferred

Only the **gateway's** DB connection is secured this slice. The `audit` and `killswitch`
services still connect to Postgres directly — routing every DB client through a client
sidecar (and making Postgres reachable *only* via mTLS) is the follow-up. gateway→Redpanda
(Kafka advertised-listeners) and production SPIRE also remain open.
