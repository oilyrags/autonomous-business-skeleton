---
status: accepted
---

# gateway/audit/data ↔ Redpanda over mTLS — beating the advertised-listener redirect

The last plaintext hop in the mesh. gateway (produce) and audit/data/killswitch
(consume) talked to Redpanda in the clear. This closes it with the same ghostunnel +
SPIRE-SVID pattern as the other hops — but Kafka needs one extra trick the DB hops did
not.

## The problem

A naive TCP tunnel (what worked for Postgres) breaks for Kafka. A client bootstraps
against the proxy, but the broker's **metadata response advertises its own address**;
the client then reconnects *directly* to that advertised address, bypassing the proxy
and the mTLS. So tunnelling only the bootstrap connection secures nothing.

## Decision

Give Redpanda a **dedicated `mtls` listener whose advertised address is the client-side
proxy**, so every redial stays on the mTLS path:

- Redpanda gains a third Kafka listener: `mtls://0.0.0.0:29093`, advertised as
  `mtls://kafka-mtls:29092` (the client proxy). Internal (`redpanda:9092`) and external
  (`localhost:19092`, host tests) listeners are unchanged.
- **`redpanda-proxy`** (ghostunnel *server*, `redpanda` SVID, uid 1008): terminates mTLS
  on `:29092`, forwards plaintext to `redpanda:29093`; `--allow-uri` the `kafka-client`
  SVID only.
- **`kafka-mtls`** (ghostunnel *client*, `kafka-client` SVID, uid 1009): a **shared**
  client proxy listening plaintext on `:29092`, tunnelling mTLS to `redpanda-proxy`;
  `--verify-uri` the `redpanda` SVID. Its service name is the advertised host, so the
  broker's redirect resolves straight back to it.
- The four bus clients (gateway, audit, killswitch, data) set `AB_KAFKA=kafka-mtls:29092`
  in the SPIFFE overlay. librdkafka bootstraps there, gets metadata advertising
  `kafka-mtls:29092`, and redials the same proxy — never the plaintext broker.

**Shared client identity (trade-off).** Unlike the DB hops (one sidecar + SVID per
service), all bus clients share the single `kafka-client` proxy identity. Per-client bus
identity would require a **separate advertised listener per client** on the broker
(a single listener can advertise only one address). Deferred; the granularity that
matters — *which agent decided* — is already carried in the event payload and the audit
hash chain, not the transport.

## Verified

- Live (`make up` then `make spire-bus-verify`): all four clients report
  `AB_KAFKA=kafka-mtls:29092`; a driven `/act` had the gateway **produce** a decision and
  both **audit** and **data** (independent consumer groups pointed at `kafka-mtls`)
  **consume** it — the allow record landed in the hash chain and `decisions_recorded_total`
  advanced. Fresh consumers reconnecting successfully is itself proof the advertised
  redirect stays on the mTLS path (else they'd have redialled `redpanda:9092`). A no-SVID
  client is rejected at `redpanda-proxy`. `spire-secure-verify` still passes (no regression
  on the other hops). CI docker job runs `spire-bus-verify`.

## Deferred

Network-isolating Redpanda so the plaintext `29093`/`9092` listeners are unreachable
except via the proxy (as `pgnet` did for Postgres); per-client bus SVIDs; Redpanda-native
TLS (would need file-delivered SVIDs via spiffe-helper for librdkafka, a bigger change).
