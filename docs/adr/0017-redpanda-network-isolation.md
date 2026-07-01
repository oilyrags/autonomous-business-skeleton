---
status: accepted
---

# Network-isolate Redpanda — no direct route to the broker

ADR-0016 put the bus hop on mTLS, but Redpanda still sat on the shared `default`
network: any app container could open a plaintext socket straight to `redpanda:9092`
(or the mTLS-backend `:29093`), bypassing the proxy. This applies the same isolation
`pgnet` gave Postgres (slice 14) so the mTLS path is the *only* route in.

## Decision

- New isolated `busnet`; **Redpanda attaches to `busnet` only** (removed from `default`).
- **`redpanda-proxy` bridges `default` + `busnet`** — it is the sole container that can
  reach the broker. App services (on `default`) have no route to `redpanda` at all; the
  service name doesn't even resolve for them, so a stray direct connection fails fast.
- The host keeps its route via the **published external listener** (`localhost:19092`):
  Docker port publishing is independent of the user-defined network, so in-process tests
  (`make check`, `make data`) are unaffected — same trade-off `pgnet` made with `55432`.
- No app-facing change: the bus clients already reach Redpanda through `kafka-mtls` →
  `redpanda-proxy` (ADR-0016). This slice only removes the plaintext shortcut.

## Verified

- Live (`make up` → `make spire-bus-verify`): bus produce/consume over mTLS still works
  (gateway produces; audit + data consume); the no-SVID client is still rejected at
  `redpanda-proxy`; and the **new isolation check passes** — `gateway` cannot open a
  socket to `redpanda:9092` *or* `redpanda:29093`. Host still reaches `localhost:19092`
  (in-process tests unaffected). `spire-secure-verify` still green (no regression).

## Result

Both stateful backends — Postgres and Redpanda — are now network-isolated, reachable
only through their mTLS proxies. Combined with ADR-0008..0016, **every service-to-service
hop is mTLS and neither datastore is directly reachable from the app network.**

## Deferred

Removing the host-published plaintext listeners entirely (prod would drop `19092`/`55432`
and drive everything through the mesh); per-client bus SVIDs; production SPIRE node
attestation (the join-token flow is dev-only).
