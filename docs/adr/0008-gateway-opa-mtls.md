---
status: accepted
---

# Extend mTLS to the gateway→OPA hop

Grow the SPIFFE mesh by one hop: the gateway's authorization call to OPA now runs over
mutual TLS, reusing the ghostunnel client+server sidecar pattern from ADR-0007.

## Decision

- New workload identity `spiffe://ab.internal/opa` (SPIRE, unix attestor uid 1003).
- **opa-proxy** (ghostunnel server, uid 1003 → opa SVID): fronts `opa:8181`, accepts only
  `--allow-uri spiffe://ab.internal/gateway`.
- **gateway-opa-proxy** (ghostunnel client, uid 1002 → gateway SVID): the gateway's
  outbound client side; `--verify-uri spiffe://ab.internal/opa`.
- The secured overlay (`docker-compose.spiffe.yml`) repoints the gateway
  (`AB_OPA_URL=http://gateway-opa-proxy:8181`) so its OPA calls go through the sidecar.
  OPA itself stays plaintext behind its proxy — no OPA TLS config needed.

## Verified (scripts/spire-secure-verify.sh; CI `docker` job)

Because the gateway can no longer reach OPA directly, a successful `agent /act` (which
requires an OPA "allow") proves the authorize decision returned over the mTLS'd OPA hop.
Confirmed: `/act` → 200 with the decision recorded, and a no-SVID client is rejected at
opa-proxy. The agent→gateway hop (ADR-0007) is verified in the same run.

## Consequences

The sidecar pattern (client + server ghostunnel, SPIFFE-ID authz, plaintext behind the
proxy) is now the repeatable template for adding hops. The still-open hops
(gateway→Postgres, gateway→Redpanda) are harder: Postgres touches several DB clients, and
Kafka's advertised-listeners break naive TCP proxying — left as future work.
