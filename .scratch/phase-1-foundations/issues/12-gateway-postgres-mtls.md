# 12 — Extend mTLS to the gateway→Postgres hop

Status: done

## What to build

Put the gateway's Postgres connection over mTLS via the ghostunnel sidecar pattern —
proving it works for a stateful TCP protocol, not just HTTP.

## Acceptance criteria

- [x] `postgres` workload identity (SPIRE, uid 1004); postgres-proxy (server) accepts only
      the gateway SVID; gateway-pg-proxy (client) trusts only the postgres SVID.
- [x] Gateway DSN repointed to the client sidecar (`sslmode=disable`); the gateway starts
      (init_db over mTLS) and `agent /act` persists a Decision over the mTLS'd DB hop.
- [x] A no-SVID client is rejected at postgres-proxy.
- [x] CI `docker` job verifies all three hops (agent→gateway, gateway→OPA, gateway→Postgres).

## Comments

**Done (2026-07-01).** ADR-0009. Two ghostunnel sidecars (postgres-proxy server uid 1004,
gateway-pg-proxy client uid 1002) TCP-tunnel the Postgres wire; `postgres` entry added to
`spire-bootstrap.sh`. Overlay repoints the gateway DSN to `gateway-pg-proxy:5432?sslmode=disable`
(TLS handled by ghostunnel). `init_db()` gained a connect-retry for sidecar-readiness races.
Verified: gateway healthy (startup DB over mTLS) + `/act` 200 (Decision persisted over mTLS) +
no-SVID rejected at postgres-proxy. `make spire-secure && make spire-secure-verify`.

**Still deferred:** route `audit`/`killswitch` DB clients through sidecars too (make Postgres
mTLS-only); gateway→Redpanda (Kafka advertised-listeners); production SPIRE.

## Blocked by

- 11 — Extend mTLS to the gateway→OPA hop
