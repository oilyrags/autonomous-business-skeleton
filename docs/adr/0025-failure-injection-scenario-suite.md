---
status: accepted
---

# Failure-injection scenario suite — Audit 12

Verification Audit 12 requires *"run the scenario suite; remediate findings."* This adds
`ab_failsim`, a runnable suite that injects each of the seven `architecture/16` failure
scenarios against the real control code and asserts the failure is **contained**.

## Decisions

- **`ab_failsim`** drives the actual controls (eval gate, tool registry, ledger, freshness)
  with injected failures — deterministic, no infra. Each scenario returns
  CONTAINED / BREACH / DEFERRED; `make failsim` exits non-zero on any BREACH (in CI).
- **Five scenarios are build-proven contained:**
  - *bad model output* → the hallucinating model is blocked by the grounding gate and its
    output can never serve; money math is deterministic (integer ledger). (`11`, AM-12)
  - *hostile prompt injection* → a sensitive tool fails closed on an untrusted-input flow and
    an over-cap refund needs maker-checker. (`10`, AM-13)
  - *bad payment* → duplicate rejected (idempotency), over-cap and **new payee** require
    approval. (AM-11)
  - *failed dependency* → a re-delivered event is applied exactly once (idempotent consumer);
    balance intact. (`04`)
  - *stale forecast* → the readiness gate refuses to serve KPIs when the warehouse is unbuilt
    or stale. (`13`, freshness)
- **Two scenarios are DEFERRED, not passed** — their components don't exist yet, and the
  suite reports them as DEFERRED so it never overclaims: DSAR erasure with legal hold
  (Compliance phase) and incident/rollback (SRE phase).

## Remediation applied

Running the suite surfaced one real gap (the standing rule: a finding auto-demotes the
process until fixed): **AM-11 "new payee → approval" was not implemented** (deferred in
ADR-0023). Fixed in `ab_ledger.core`: `Transaction.payee` + an `APPROVED_PAYEES` allow-list;
`approval_reason`/`validate` now require a checker for a payment to a payee not on the list,
even under the cap (+3 core tests). The `bad_payment` scenario now exercises it.

## Verified

- `make failsim` → 5 contained, 0 breach, 2 deferred. Tests (+5): all seven scenarios run;
  no breaches among implemented ones; the five expected scenarios are contained; exactly the
  DSAR + incident scenarios are deferred; the CLI exits 0. lint + mypy strict clean.

## Audit impact

**Audit 12 (failure-injection) → PASS (build-proven)** for the implemented control surface,
with the DSAR-erasure and incident-rollback scenarios explicitly deferred to their phases.
`architecture/16` updated; **all five originally-CONDITIONAL audits (4, 6, 7, 9, 12) now have
build proofs — 0 remain CONDITIONAL.**

## Deferred

Implement the DSAR erasure/legal-hold flow and the incident/rollback (error-budget freeze +
auto-rollback) components, then flip those two scenarios from DEFERRED to CONTAINED.
