# 07 — Harden OIDC: issuer/audience verification + Vault for secrets

Status: done

## What to build

Close the two ADR-0004 skeleton simplifications. SPIFFE/mTLS stays deferred.

**A. Issuer + audience verification.** Pin Keycloak's frontend hostname so the
`iss` claim is stable across host/in-container access; add an audience mapper so
tokens carry `aud: ab-gateway`; the gateway verifies both `iss` and `aud`.

**B. Vault for secrets.** Run Vault (dev) and move the Keycloak client secrets out
of compose env into Vault KV; the agent and tests fetch the secret from Vault at
use time (no client secret in app env).

## Acceptance criteria

- [ ] Gateway verifies `iss` (fixed frontend URL) and `aud` (`ab-gateway`); a token
      with the wrong issuer/audience is rejected.
- [ ] Client secrets are read from Vault by the agent + tests; not present in the
      app/compose env for those consumers.
- [ ] In-process suite + containerized smoke still green; CI brings up Vault + seeds it.

## Blocked by

- 06 — Real OIDC identity (Keycloak)

## Comments

**Done (2026-06-30).** ADR-0005. Stage A: pinned Keycloak frontend hostname so `iss` is stable; audience mapper stamps `aud: ab-gateway`; gateway verifies signature + `iss` + `aud` + expiry. Verified a real token carries `iss=http://localhost:18083/realms/ab`, `aud=[ab-gateway,account]`, `azp=client_id`. Stage B: Vault (dev) holds client secrets at `secret/ab/clients`; `ab_common.secrets.get_client_secret` reads KV v2; agent + tests fetch from Vault (no client secret in app env). `make seed-vault`; up-infra/up + CI seed Vault. Verified: 11 in-process tests + containerized smoke green (agent pulls secret from Vault → token from Keycloak → gateway validates iss/aud → 200). SPIFFE/mTLS remains the open zero-trust item.
