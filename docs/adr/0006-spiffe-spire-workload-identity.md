---
status: accepted
---

# SPIFFE/SPIRE workload identity + agent↔gateway mTLS (tracer)

Introduce **SPIFFE workload identity** via **SPIRE** so services authenticate to each
other with short-lived X.509 SVIDs (mutual TLS), toward the zero-trust target. This
slice is the **thin tracer** on the highest-value hop (agent → gateway); other hops and
full-mesh mTLS are follow-ups.

## Decisions

- **Trust domain** `ab.internal`. SPIRE server + one SPIRE agent, run under the
  compose **`spiffe` profile** so they don't affect the default app stack.
- **Node attestation:** `join_token` (dev), with a node-alias entry
  (`spiffe://ab.internal/node`) so workload entries have a stable parent. Bootstrapped
  by `scripts/spire-bootstrap.sh`.
- **Workload attestation:** the **`unix` attestor keyed on UID** — `gateway` = uid 1002,
  `agent` = uid 1001. This works across containers over the shared Workload-API socket
  because `SO_PEERCRED` provides the UID directly, avoiding the docker-attestor +
  PID-namespace complexity that makes SPIRE-in-compose painful.
- **Image:** a small shell-capable image (`Dockerfile.spire`, debian + SPIRE musl
  binaries + openssl), since SPIRE's official images are distroless and the join-token
  flow needs a shell.

## Verified (scripts/spire-verify.sh, CI `spiffe` job)

- SPIRE issues the correct SVID per identity: uid 1002 → `spiffe://ab.internal/gateway`,
  uid 1001 → `spiffe://ab.internal/agent`.
- A **mutual-TLS handshake** between the agent and gateway SVIDs succeeds
  (`Verification: OK`); a client presenting **no** SVID is rejected.

## Deferred (follow-ups, explicitly not in this slice)

- **Wiring the SVIDs into the live service calls** — the `agent`/`gateway` Python
  services still call each other over plain HTTP. Doing mTLS in-process needs SVID
  files fetched per service (sidecar or `spire-agent api fetch -write`), uvicorn TLS,
  and httpx client certs. App-layer **SPIFFE-ID authorization** (peer must be
  `spiffe://ab.internal/agent`) is awkward through uvicorn/ASGI and is best done with a
  **SPIFFE-aware proxy (ghostunnel/Envoy)** — the recommended next step.
- SVID rotation handling, production SPIRE (non-`join_token` node attestation), and
  extending mTLS to the other hops + third-party infra.
