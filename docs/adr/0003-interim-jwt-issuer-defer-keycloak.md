---
status: superseded by ADR-0004
---

# Walking skeleton uses a minimal custom JWT issuer; Keycloak/SPIFFE deferred

Agent identity in the first slice is a small in-house `identity` service issuing short-lived signed JWTs backed by a revocation list, rather than standing up Keycloak/Zitadel or SPIFFE/mTLS. This keeps the foundational slice thin while still proving the property the kill switch depends on: an **authenticated, revocable principal**.

This is recorded because a future reader will otherwise wonder why a custom issuer exists instead of the standard IdP named in `architecture/10_security_architecture.md`.

## Considered Options

- **Minimal custom JWT issuer** (chosen, interim) — thinnest real thing that gives authenticated + revocable identity.
- **Keycloak/Zitadel now** — real OIDC from day one, no rework, but heavy for a first slice.
- **SPIFFE/mTLS now** — closest to the zero-trust target, most complex to bootstrap.

## Consequences

The issuer is explicitly **throwaway/replaceable**. The gateway's token-validation interface must not leak issuer specifics, so swapping in Keycloak (humans) + SPIFFE/mTLS (agents) in a later slice is a contained change. Target end state is unchanged from `10_security_architecture.md`; only the sequencing is deferred. Superseding ADR to be written when the real IdP lands.
