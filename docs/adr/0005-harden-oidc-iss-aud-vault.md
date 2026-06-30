---
status: accepted
---

# Harden OIDC: verify iss/aud, and source client secrets from Vault

Closes the two skeleton simplifications noted in ADR-0004.

- **Issuer/audience verification.** Keycloak's frontend hostname is pinned
  (`KC_HOSTNAME=http://localhost:18083`, `KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true`) so the
  token `iss` is a stable string regardless of whether the token was fetched from the
  host or in-container. An audience mapper on each client stamps `aud: ab-gateway`.
  The gateway now verifies signature (JWKS), `iss`, `aud`, and expiry.
- **Vault for secrets.** Agent client secrets live in Vault (KV v2 at
  `secret/ab/clients`), not in app/compose env. The agent and tests fetch the secret
  from Vault at use time (`ab_common.secrets`).

## Why pin the hostname (non-obvious)

A Keycloak token's `iss` is its frontend URL. Without pinning, a token fetched via
`localhost:18083` (tests) and one fetched via `keycloak:8080` (in-container) would carry
different `iss` values, so a single `iss` check couldn't pass both. Pinning the frontend
URL fixes `iss`; `KC_HOSTNAME_BACKCHANNEL_DYNAMIC` lets in-container clients still reach the
token endpoint by service name. The JWKS URL is configured separately per environment.

## Consequences / still deferred

- Vault runs in **dev mode** and Keycloak still has the client secrets in its own realm
  config (inherent — the IdP must know them); Vault removes them from the *app* surface.
- **SPIFFE/mTLS** (service-to-service workload identity) remains the open item toward the
  zero-trust target, as its own future slice. Production Keycloak/Vault modes are follow-up.
