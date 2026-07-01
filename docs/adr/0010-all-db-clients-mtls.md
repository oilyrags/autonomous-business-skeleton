---
status: accepted
---

# Route all app DB clients through mTLS sidecars

Completes the DB story from ADR-0009: every application service that talks to Postgres now
does so over mutual TLS with its own SPIFFE identity, not just the gateway.

## Decision

- New workload identities `spiffe://ab.internal/audit` (uid 1005) and
  `spiffe://ab.internal/killswitch` (uid 1006).
- Each gets a ghostunnel **client** sidecar (`audit-pg-proxy`, `killswitch-pg-proxy`) to
  Postgres, mirroring `gateway-pg-proxy`. The shared `postgres-proxy` now allows all three
  DB clients: `--allow-uri` gateway / audit / killswitch.
- The secured overlay repoints each service's DSN to its own sidecar
  (`sslmode=disable`; TLS by ghostunnel).

## Verified (scripts/spire-secure-verify.sh; CI `docker` job)

In the secured topology: `agent /act` persists a Decision (gateway→Postgres over mTLS), the
**audit** service serves `/audit` from its DB (audit→Postgres over mTLS), and the
**killswitch** service `/activate` writes its control row (killswitch→Postgres over mTLS).
No-SVID clients are rejected at the proxies.

## Scope / caveat

This routes **all app DB clients** over mTLS, each with a distinct authorized identity.
Postgres is **not yet hard-restricted to mTLS-only**: its plaintext port is still reachable
inside the compose network (the proxies target it) and published to the host for the
in-process test suite. True mTLS-only enforcement needs Postgres-native TLS + client-cert
auth, or a network policy that permits only `postgres-proxy` — left as follow-up, along with
gateway→Redpanda and production SPIRE.
