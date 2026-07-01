# 09 — Route agent→gateway over mTLS (ghostunnel sidecars)

Status: done

## What to build

The ADR-0006 follow-up: actually route the live agent→gateway call over mutual TLS
backed by SPIFFE SVIDs, with SPIFFE-ID authorization, via ghostunnel sidecars.

## Acceptance criteria

- [x] gateway-proxy (server) + agent-proxy (client) fetch SVIDs from SPIRE (uid-attested)
      and enforce SPIFFE-ID authz (`--allow-uri` / `--verify-uri`).
- [x] A live request via agent-proxy reaches the real gateway over mTLS; a no-SVID client
      is rejected.
- [x] The full business flow (agent `/act` → record a Decision) works over the mTLS path.
- [x] Opt-in (compose `spiffe` profile + `docker-compose.spiffe.yml` overlay); default
      stack unchanged. CI `docker` job verifies the mTLS path.

## Comments

**Done (2026-07-01).** ADR-0007. Two ghostunnel sidecars (`spiffe` profile): gateway-proxy
(server, uid 1002 → gateway SVID, `--allow-uri spiffe://ab.internal/agent`) and agent-proxy
(client, uid 1001 → agent SVID, `--verify-uri spiffe://ab.internal/gateway`), both fetching
SVIDs via the SPIRE Workload API. Two gotchas solved: **shared PID namespace**
(`pid: service:spire-agent`) so SPIRE's peertracker can resolve the caller's `/proc` for
UID attestation cross-container ("could not resolve caller information" otherwise); and
ghostunnel's `--unsafe-target`/`--unsafe-listen` for the container-internal plaintext legs.
Verified: `/health` over mTLS = 200, no-SVID rejected, and agent `/act` records a Decision
over mTLS (audit allow). `make spire-mtls && make spire-mtls-verify`;
`docker-compose.spiffe.yml` repoints the agent for the full-flow demo.

**Still deferred:** other hops + third-party infra mTLS; production SPIRE; rotation drills.

## Blocked by

- 08 — SPIFFE/mTLS tracer
