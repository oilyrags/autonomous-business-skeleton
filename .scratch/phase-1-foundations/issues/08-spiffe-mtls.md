# 08 — SPIFFE/mTLS workload identity (thin tracer: agent↔gateway)

Status: done

## What to build

Introduce SPIFFE workload identity via SPIRE and prove mutual TLS on the highest-value
hop (agent → gateway), without re-TLS'ing third-party infra. Scope is the thin tracer
(per the grilling); full mesh + app-integration are follow-ups.

## Acceptance criteria

- [x] SPIRE server + agent run in compose (opt-in `spiffe` profile), workloads attested.
- [x] SPIRE issues the right SVID per identity (gateway=uid 1002 → `.../gateway`,
      agent=uid 1001 → `.../agent`).
- [x] A mutual-TLS handshake between the agent and gateway SVIDs succeeds; a no-SVID
      client is rejected.
- [x] Verifiable via `make spire-up && make spire-verify`; CI `spiffe` job runs it.
- [x] Default app stack unaffected (SPIRE behind a compose profile).

## Comments

**Done (2026-07-01).** ADR-0006. Solved the hard part — SPIRE workload attestation in
compose — with the **unix attestor keyed on UID** (agent=1001, gateway=1002), which works
cross-container over the shared Workload-API socket via `SO_PEERCRED`, avoiding the
docker-attestor/PID-namespace pain. Shell-capable `Dockerfile.spire` (SPIRE musl binaries
+ openssl) drives the join-token bootstrap. `scripts/spire-bootstrap.sh` +
`scripts/spire-verify.sh`; Make `spire-up`/`spire-verify`; CI `spiffe` job. Verified:
correct SVIDs + `Verification: OK` mTLS handshake + no-cert rejected.

**Deferred (in ADR-0006):** wiring the SVIDs into the live uvicorn/httpx service calls and
app-layer SPIFFE-ID authorization (best via a ghostunnel/Envoy SPIFFE-aware proxy); SVID
rotation; production SPIRE; other hops. The services still call each other over plain HTTP
today — this slice establishes and proves the identity+mTLS mechanism, not full enforcement.

## Blocked by

- 07 — Harden OIDC (Vault + iss/aud)
