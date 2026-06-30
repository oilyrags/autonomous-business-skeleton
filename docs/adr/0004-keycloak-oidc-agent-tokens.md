---
status: accepted
---

# Agent tokens are issued by Keycloak (OIDC); the gateway validates via JWKS

Supersedes ADR-0003. The interim in-house HS256 issuer is replaced by **Keycloak** as the OIDC provider. Each agent is a Keycloak **client**; agents obtain tokens via the **client-credentials** grant. The gateway validates **RS256** tokens against Keycloak's **JWKS** endpoint (no shared secret) and reads the **`azp`** claim (= the client_id) as the principal — which the OPA policy keys on.

This is the "OIDC token issuance" slice only. SPIFFE/mTLS (service-to-service workload identity) and Vault (secret storage) remain deferred to their own slices.

## Considered Options

- **Keycloak** (chosen) — mature, declarative realm import for reproducible compose config, standard JWKS/RS256.
- **Zitadel** — modern/lighter, but reproducible bootstrap is more work (API/Terraform vs realm file).

## Consequences

- Validation is JWKS/RS256 only — one path. Tests and the `agent` service fetch **real tokens from Keycloak** via client-credentials (Keycloak is now part of the infra `make up-infra`/CI bring up). The HS256 `issue_token` is removed.
- The `identity` service's role narrows to **revocation** (`/revoke`) + health; Keycloak issues tokens. App-level revocation (slice 03) still layers on top — a revoked principal is denied even with a valid Keycloak token.
- **Skeleton simplifications (documented, not production-final):** the gateway verifies signature + expiry but not `iss`/`aud`, to sidestep Keycloak's host/issuer-vs-JWKS-URL mismatch across host (tests) and in-container access; client secrets live in compose env (not Vault yet); realm uses `start-dev`. Hardening (issuer/audience checks, Vault-managed secrets, production Keycloak mode) is follow-up work.
