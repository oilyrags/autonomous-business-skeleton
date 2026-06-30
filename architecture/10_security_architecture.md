# 10 — Security Architecture (safe-autonomy control plane)

Zero-trust by default. Agents are **first-class principals** with the same authentication, authorization, logging, and revocation rigor as humans — plus AI-specific defenses (prompt injection, exfiltration, runaway action).

## 1. Identity & access

- **Principals:** humans (via Keycloak/Zitadel OIDC) and agents (workload identity, short-lived mTLS certs / SPIFFE-style). Every principal has a unique id, role set, and lifecycle.
- **AuthN:** OIDC for humans; mutual-TLS + signed workload identity for agents and services. No long-lived static credentials.
- **AuthZ:** **RBAC + ABAC via policy-as-code (OPA/Cedar).** Default-deny. Every tool call, API call, and event publish is a `POST /authz/evaluate` decision with attributes {principal, action, resource, purpose, dataClass, authorityLevel}.
- **Least privilege:** agents receive only the tools/scopes their charter requires (`05`). Periodic automated access review demotes unused grants.

## 2. Agent action lifecycle (every action)

```
intend → authZ check (OPA) → guardrail pre-check → tool call (registered only)
       → result post-check (output filter) → audit event → (approval if matrix requires)
```
Invariant: **authenticated, authorized, logged, explainable, revocable.** An action missing any of these does not execute.

## 3. Secrets & encryption

- Secrets in **Vault**; SOPS for config-as-code secrets; never in code/logs/traces (CI secret-scan + log redaction).
- Encryption at rest (storage-level + app-level for personal/financial) and in transit (mTLS everywhere).
- **KMS** with key rotation; envelope encryption; separate keys per data class.

## 4. Network & runtime

- Network segmentation (per-context namespaces, default-deny network policies). Agent runtimes egress-restricted to an allow-list (anti-exfiltration).
- Runtime protection: Falco (syscall anomaly), admission control (no unsigned images), pod security standards.

## 5. Supply chain

- SBOM (Syft) for every artifact; vulnerability scan (Grype/Trivy); SAST (Semgrep); DAST (OWASP ZAP); dependency + container scanning in CI. Critical findings block release.
- Image signing + verification (cosign-style); GitOps with signed commits.

## 6. AI-specific defenses

**Prompt injection (every externally-triggered agent flow):**
- Untrusted input (emails, tickets, web content, documents) is tagged `untrusted` and never concatenated into a privileged instruction context without delimiting + an instruction-hierarchy guard.
- Tool calls triggered from untrusted input require the action to be on the agent's allow-list *and* below its authority level; sensitive tools (money, PII export, irreversible) **fail closed** and require approval regardless.
- Output filtering: detect/redact secrets, system-prompt leakage, and injected instructions before results propagate.

**Data exfiltration:**
- Egress allow-list per agent; large/anomalous data movements trip a circuit breaker.
- DLP on outbound channels (email, API) for personal/financial classes.
- Retrieval is scoped: an agent can only retrieve from knowledge collections its principal is authorized for.

**Runaway action:**
- **Rate limits** (per agent, per tool), **spend limits** (hard caps enforced deterministically in Finance + gateway cost budget), **circuit breakers** (auto-trip on error spikes/anomalies).

## 7. Kill switch (launch blocker)

| Scope | Effect | Who | Control |
|---|---|---|---|
| **global** | Revoke all agent credentials; gateway stops routing; runtimes halt tool calls within SLA | human-approved (dual control); any agent may *request* | drilled regularly; RTO measured |
| **context** | Halt one context's agents | CISO Agent (L4) | logged, reviewed |
| **agent** | Revoke one agent | CISO/Threat agent (L4) | logged |

`KillSwitchActivated` is a priority broadcast; the gateway and runtimes treat it as fail-closed. **A working, drilled kill switch is a launch blocker** (verified in `16`). Deactivation is dual-control human.

## 8. Threat modeling, SIEM, IR, BC/DR

- Threat models per context (STRIDE), refreshed on major change; red-team agent + scheduled human red-teaming.
- SIEM ingests audit log + traces + infra telemetry; detections → `ThreatDetected`.
- Incident response runbooks (shared with QA `03`); BC/DR: backups, tested restore, RPO/RTO targets, multi-AZ; DR drills.

## 9. Audit log (system of record)

- Append-only, immutable, tamper-evident (hash-chained), 18mo hot + 5y cold.
- Every tool call, authZ decision, approval, model invocation, and money movement emits an `AuditEvent`. This is the backbone evidence for Compliance and Finance audits.

## Guardrails (binding)

1. Every agent action authenticated, authorized, logged, explainable, revocable.
2. Least privilege, default-deny.
3. Irreversible/high-impact/legally-binding/threshold-exceeding actions require approval (`06`).
4. A working kill switch is a launch blocker.
5. No secret in code/logs. PII never in plaintext logs.
6. Every externally-triggered agent flow has prompt-injection + exfiltration controls.
