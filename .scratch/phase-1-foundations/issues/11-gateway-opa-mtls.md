# 11 — Extend mTLS to the gateway→OPA hop

Status: done

## What to build

Put the gateway→OPA authorization call over mTLS, reusing the slice-09 ghostunnel
client+server sidecar pattern. OPA stays plaintext behind its proxy.

## Acceptance criteria

- [x] `opa` workload identity (SPIRE, uid 1003); opa-proxy (server) accepts only the
      gateway SVID; gateway-opa-proxy (client) trusts only the opa SVID.
- [x] The gateway calls OPA through its client sidecar (`AB_OPA_URL` repointed in the
      secured overlay); a live `agent /act` (needs an OPA allow) returns 200 → proves the
      authorize flowed over the mTLS'd OPA hop.
- [x] A no-SVID client is rejected at opa-proxy.
- [x] CI `docker` job verifies both hops (agent→gateway + gateway→OPA).

## Comments

**Done (2026-07-01).** ADR-0008. Two more ghostunnel sidecars under the `spiffe` profile
(opa-proxy server uid 1003, gateway-opa-proxy client uid 1002), plus the `opa` entry in
`spire-bootstrap.sh`. Secured overlay repoints the gateway's `AB_OPA_URL` to the client
sidecar. `make spire-secure && make spire-secure-verify`. Verified: `/act` → 200 (decision
recorded) with OPA reached only via mTLS, and no-SVID rejected at opa-proxy. The
agent→gateway hop is verified in the same flow.

**Still deferred:** gateway→Postgres (touches several DB clients) and gateway→Redpanda
(Kafka advertised-listeners break naive TCP proxying); production SPIRE.

## Blocked by

- 09 — Route agent→gateway over mTLS
