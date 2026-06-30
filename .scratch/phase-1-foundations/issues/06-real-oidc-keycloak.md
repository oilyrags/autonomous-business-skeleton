# 06 — Real OIDC identity (Keycloak), supersede interim JWT issuer

Status: done

## What to build

Replace the interim HS256 issuer (ADR-0003) with **Keycloak** as the OIDC provider
(ADR-0004). Each agent is a Keycloak client; agents get tokens via the
client-credentials grant; the gateway validates RS256 tokens against Keycloak's
JWKS and reads `azp` (= client_id) as the principal. Scope is OIDC token issuance
only — SPIFFE/mTLS and Vault stay deferred.

## Acceptance criteria

- [x] Gateway validates RS256 via JWKS (no shared secret); principal = `azp`.
- [x] Agents/tests obtain real tokens via client-credentials from Keycloak.
- [x] Keycloak runs in compose with a declarative realm import (clients
      `executive.cmo_agent`, `executive.intern_agent`).
- [x] In-process suite (11) passes with real tokens; containerized smoke works.
- [x] `identity` service narrows to revocation + health; app-level revocation still
      denies a revoked principal holding a valid Keycloak token.
- [x] CI brings up Keycloak and waits for the realm in both jobs.

## Comments

**Done (2026-06-30).** Keycloak 26 in compose (`start-dev --import-realm`, realm
`config/keycloak/ab-realm.json`, host port 18083). New `ab_identity.oidc.fetch_token`
(client-credentials); `ab_identity.tokens.validate_token` now uses `PyJWKClient`
(RS256, `pyjwt[crypto]`). Per-env URLs (host for tests, `keycloak:8080` in-container)
sidestep the issuer/JWKS host mismatch; issuer/audience checks omitted in the
skeleton (documented in ADR-0004). `make_token` test fixture mints real tokens;
all 4 test modules updated. Verified: 11 in-process tests + containerized smoke
(agent client-credentials → gateway JWKS → 200). ADR-0003 marked superseded.

## Blocked by

- 05 — Containerize the five services
