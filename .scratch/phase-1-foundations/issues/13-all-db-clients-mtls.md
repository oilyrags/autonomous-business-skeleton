# 13 — Route all app DB clients (audit, killswitch) through mTLS sidecars

Status: done

## What to build

Complete the DB mTLS story: give `audit` and `killswitch` their own client sidecars +
SPIFFE identities so every app service reaches Postgres over mTLS, not just the gateway.

## Acceptance criteria

- [x] `audit` (uid 1005) + `killswitch` (uid 1006) workload identities; postgres-proxy
      allows all three DB clients (gateway/audit/killswitch).
- [x] audit + killswitch DSNs repointed to their own client sidecars in the overlay.
- [x] Verified: audit service reads over mTLS; killswitch service writes over mTLS;
      gateway persists over mTLS; no-SVID rejected. CI verifies.

## Comments

**Done (2026-07-01).** ADR-0010. Two client sidecars (audit-pg-proxy uid 1005,
killswitch-pg-proxy uid 1006); `postgres-proxy` `--allow-uri` extended to audit + killswitch;
entries added to `spire-bootstrap.sh`; overlay repoints audit/killswitch DSNs. Verified:
`/act` 200 (gateway DB over mTLS), `/audit` read = 1 record (audit DB over mTLS), `/activate`
= activated (killswitch DB over mTLS), no-SVID rejected at proxies. `make spire-secure &&
make spire-secure-verify`; CI `docker` job verifies.

**Caveat (ADR-0010):** all app DB clients now use mTLS, but Postgres isn't hard-restricted to
mTLS-only (plaintext port stays for host tests + the proxy targets it). True enforcement =
Postgres-native TLS or a network policy — follow-up, with gateway→Redpanda + production SPIRE.

## Blocked by

- 12 — Extend mTLS to the gateway→Postgres hop
