---
status: accepted
---

# Enforce agent→gateway mTLS with ghostunnel sidecars

Completes the ADR-0006 follow-up: route the **live** agent→gateway traffic over mutual
TLS backed by SPIFFE SVIDs, with SPIFFE-ID authorization — without changing the app code.

## Decision

Two **ghostunnel** sidecars (under the compose `spiffe` profile):

- **gateway-proxy** (server, uid 1002): terminates mTLS in front of `gateway:8000`,
  presents the gateway SVID, and only accepts clients whose SVID is
  `--allow-uri spiffe://ab.internal/agent`.
- **agent-proxy** (client, uid 1001): listens plaintext for the agent, dials
  `gateway-proxy` over mTLS presenting the agent SVID, and only trusts a server whose
  SVID is `--verify-uri spiffe://ab.internal/gateway`.

Both fetch and rotate their SVIDs from the SPIRE Workload API
(`--use-workload-api-addr`), attested by UID (ADR-0006). The app services keep speaking
plain HTTP; the sidecars add identity + encryption. Repointing the agent
(`AB_GATEWAY_URL=http://agent-proxy:8000`, `docker-compose.spiffe.yml`) sends real
business calls over the mTLS path.

## Non-obvious gotchas (why the config looks the way it does)

- **Shared PID namespace.** The sidecars run `pid: "service:spire-agent"`. SPIRE's
  peertracker resolves a caller via `/proc/<pid>`; across separate PID namespaces that
  fails with "could not resolve caller information". Sharing the agent's PID namespace
  lets UID attestation work cross-container.
- **`--unsafe-target` / `--unsafe-listen`.** ghostunnel refuses non-localhost plaintext
  hops by default; here the plaintext legs are container-internal on the compose network,
  so the guards are explicitly waived.

## Verified (scripts/spire-mtls-verify.sh; CI `docker` job)

- A live request via `agent-proxy` reaches the real gateway over mTLS (`/health` → 200).
- A direct TLS client with **no** SVID is rejected.
- The full business flow works over mTLS: agent `/act` → agent-proxy → gateway-proxy →
  gateway records a Decision → 200.

## Still deferred

Extending mTLS to the other hops (gateway→OPA/Postgres/Redpanda, etc.) and to third-party
infra; production SPIRE node attestation; SVID-rotation drills.
