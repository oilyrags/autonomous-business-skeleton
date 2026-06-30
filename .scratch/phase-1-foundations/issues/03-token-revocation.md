# 03 — Revoked agent token fails immediately

Status: done

## What to build

Revocation independent of token expiry. After an agent is authenticated and working, calling `identity`'s revoke endpoint for that principal causes the gateway to reject the agent's **next** tool call immediately (the gateway checks revocation on every call, not just signature/expiry). This is the property the kill switch builds on.

## Acceptance criteria

- [ ] A previously-working agent token is rejected by the gateway on the first call after revocation, without waiting for token expiry.
- [ ] The rejected call performs no side effect and is audited.
- [ ] Revocation state lives in `identity` (outside the gateway), so the gateway trusts an external source of truth.

## Blocked by

- 01 — Happy-path tracer

## Comments

**Done (2026-06-30).** `ab_identity.revocation` (Postgres `revoked_principals`) + `POST /revoke`; gateway checks `is_revoked(principal)` on every call right after authentication and denies (403 "credential revoked") + audits. Tests: revoked token fails on the next call with no side effect (chain intact); other agents unaffected. ruff + mypy(24 files) + 7 tests green.
