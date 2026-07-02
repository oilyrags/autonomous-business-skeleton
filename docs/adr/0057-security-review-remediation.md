---
status: accepted
---

# Security-review remediation (VULN-001 … VULN-007)

A senior-appsec-style review (OWASP Top 10 / CWE Top 25 lens) of the security-critical paths —
gateway auth/authz, JWT validation, the ledger money path, the console mutations, the kill-switch
service, the audit chain, secrets/config — found one systemic pattern: **authorization was enforced
at the transport/policy edge but not re-bound to the caller's identity at the point of the sensitive
action.** Seven findings were fixed in priority order, each as its own tested slice. The review also
confirmed strong existing controls (RS256 JWT validation with iss/aud/exp; parameterized SQL;
arg-list subprocess; Jinja2 autoescape; fail-closed kill switch + revocation in the gateway;
deterministic ledger cap/maker-checker/allow-list/idempotency; clean secret hygiene; current deps).

## Fixes

- **VULN-001 (Critical) — console had no auth.** The control plane mutated governed state (halt the
  fleet, approve L5 decisions) with no authentication, authorization, or CSRF defense, and a
  hardcoded `console.operator` actor. Now every route requires a signed operator identity
  (`ab_common/operator_identity.py`, HMAC-SHA256 over `id:role`, verified with a shared secret so a
  caller bypassing the proxy can't forge one); mutations additionally require a mutating role and an
  Origin check and record the real operator id. `/metrics` stays open for Prometheus (aggregate
  gauges; network-restricted). CWE-306/352/862, A01.

- **VULN-002 (High) — cross-tenant fund access.** `business_id` flowed from the agent's request with
  no principal↔business binding, and never reached OPA. New default-deny grants
  (`ab_gateway/authz.py`) bind each principal to the tenants it serves; enforced in
  `transfer_payment`/`_gate_business_spend`/`write_decision` and for every tool at the gateway, and
  `business_id` now rides in the OPA input (policy `agent_businesses`). CWE-639/284, A01.

- **VULN-003 (High) — self-asserted governance metadata.** Agent-supplied `authority_level` /
  `approval_status` were persisted and emitted unchecked. Now clamped to the principal's authority
  ceiling, and a self-declared human-approval status is downgraded to `autonomous_within_policy`
  (agents can never self-approve) — in both the decision registry and the `AgentDecisionMade` event.
  CWE-915/807, A04/A08.

- **VULN-004 (Medium) — kill-switch `/activate` trusted any mesh peer.** Now requires a signed
  operator identity in a mutating role and records the *verified* caller as `activated_by` (the body
  can't spoof it; an agent lacking the secret can't halt the fleet). The console forwards the
  operator's signed identity on the hop. CWE-306/862, A01.

- **VULN-005 (Low) — insecure secret defaults.** `pg_dsn`, `vault_token`, and the operator-identity
  and audit keys carried weak known defaults. Secret-bearing settings now fail closed outside dev
  (`_secret()` raises at import unless `AB_ENV` is a dev env). CWE-1188/798.

- **VULN-006 (Low) — unkeyed audit chain + append race.** The chain link is now HMAC-SHA256 under a
  key held outside the DB, so a DB-write adversary cannot re-forge it; `append` serializes on a
  transaction-scoped advisory lock so concurrent writers can't fork the chain. CWE-354.

- **VULN-007 (Info) — OPA outage produced an unhandled 500.** `authorize` now raises a typed
  `OpaUnavailable`; the gateway maps it to a **503 audited deny** (fail closed *and* recorded).

## Consequences

- One signed-operator-identity definition is shared by the console and the kill-switch service; the
  trusted proxy signs it and the services verify. Local `make console-serve` now needs those headers
  (see `docs/console.md`).
- Authorization is bound to identity at the point of action, in addition to the OPA policy —
  defense in depth. New principals are default-deny (no tenant, authority ceiling 0).
- 27 new tests (all infra-free): console auth/role/CSRF/attribution, gateway tenant + authority +
  no-self-approval, kill-switch actor authz, fail-closed secrets, keyed audit chain, OPA-outage deny.

## Not done (follow-ups)

- Load `agent_businesses` + authority ceilings from the agent registry / OPA data per deployment
  rather than the seeded map; add the remaining 71 agents.
- Periodic external anchoring of the audit head hash (belt-and-suspenders beyond the HMAC).
- Wire the operator OIDC login in the reverse proxy that mints the signed headers.
