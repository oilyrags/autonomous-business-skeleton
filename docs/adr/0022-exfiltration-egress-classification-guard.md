---
status: accepted
---

# Exfiltration guard: data-classification egress clearance

Continues Audit 6 hardening. ADR-0021 added the prompt-injection control (sensitive tools
fail closed on untrusted input); this adds the **exfiltration** control the audit also
requires: sensitive data must not leave the trust boundary through a channel not cleared
for it (architecture/09–10).

## Decisions

- **Egress tools carry a clearance.** `ToolSpec` gains `egress: bool` and
  `clearance: DataClassification` (the highest sensitivity the tool may transmit).
- **Requests declare data sensitivity.** `ToolCallRequest.data_classification`
  (default `internal`) — the classification of the content the agent is acting on.
- **Egress guard.** `tools.exfiltration_blocked` ranks classifications
  (`public<internal<confidential<personal=financial`); in `/tool-call`, after OPA and the
  untrusted-input gate, an **egress tool is refused when the data classification exceeds its
  clearance**. So even an authorized `notify.external` cannot send `personal`/`financial`
  data. The denial is audited and the tool never runs (fail closed).
- **Demo egress tool** `notify.external` (egress, sensitive, clearance `internal`,
  `side_effect=irreversible`) persists to a new append-only `outbox` table; OPA now
  authorizes it for the skeleton agent so the guard downstream is the thing under test.
- **Tool contracts gate event emission.** Added `ToolSpec.emits_decision`; the gateway
  emits `AgentDecisionMade` only for decision-recording tools, so an egress send doesn't
  inflate the decision stream / KPIs. `GET /tools` now advertises `egress` + `clearance`.

## Verified

- Infra-free (+2): the egress guard's classification matrix (internal/public pass;
  confidential/personal/financial blocked); a non-egress tool is never exfiltration-blocked.
- Integration (against `make up-infra`, +2): `notify.external` with `data_classification=
  personal` → **403 "…exceeds egress clearance…", nothing written to `outbox`, denial
  audited, hash chain intact**; the same call with `internal` → 200 and one `outbox` row.
  Full gateway suite (29) green — behaviour-preserving. lint + mypy strict clean.

## Audit impact

**Audit 6 (security) → PASS (build-proven).** All three build-time controls now have proofs
+ tests: kill-switch drill within SLA (slice 04), prompt-injection fail-closed (ADR-0021),
and exfiltration egress guard (this ADR). The injection/exfiltration suites are
representative and extensible (see Deferred). `architecture/16` updated; CONDITIONAL 4 → 3.

## Deferred

Content-based DLP (scan payloads/outputs for secrets/PII, not just a declared label);
per-destination egress allow-lists; inferring classification from data instead of trusting
the caller's label; broader adversarial injection/exfiltration corpora.
