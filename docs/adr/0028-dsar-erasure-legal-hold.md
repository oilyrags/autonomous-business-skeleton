---
status: accepted
---

# DSAR erasure with legal hold — flips failure-injection scenario 5 to CONTAINED

Failure-injection scenario 5 (`architecture/16`) was DEFERRED because no DSAR flow existed.
This adds a deterministic erasure-decision engine, so the scenario is now build-proven
CONTAINED (6 of 7 scenarios; only incident/rollback remains deferred).

## Decisions

- **`ab_compliance.dsar`** decides the erasure plan from the `08` RoPA (GDPR Art.17). For a
  subject, each **personal** data element is either erased or **retained under legal hold** —
  retained when its lawful basis is `legal_obligation` or its retention policy blocks erasure
  (`legal_hold_policies` reads the RoPA descriptions: "legal_obligation" / "Erasure blocked").
- **Retention is evidenced.** Each retained item is itemized with `{dataElement, lawfulBasis,
  retentionPolicy, reason}`; `ErasurePlan.evidenced` requires every retained item to carry its
  basis + policy — the refusal-to-erase is justified (Art.17(3)(b): erasure doesn't apply where
  processing is necessary to meet a legal obligation, e.g. financial records kept 10y for tax).
- **Decision, not deletion.** The engine produces the plan; propagating actual deletes across
  live stores is deferred (the skeleton has no customer stores yet). This matches how the
  compliance gate reasons over the RoPA without a live customer DB.
- **Scenario wired.** `ab_failsim`'s `dsar_erasure_with_legal_hold` now runs the engine and
  asserts: erasure propagated (non-empty), a financial record retained under hold, and the plan
  evidenced → CONTAINED.

## Verified

- On the shipped `08`: 6 elements erased (consent/legitimate-interest/contract-based), 2
  retained under legal hold (`account.billing_contact` via `financial_retention`;
  `dsar.subject_identity` via `legal_obligation`), evidenced. `make failsim` → **6 contained,
  0 breach, 1 deferred**. Tests (+4): legal-hold detection; erasure propagates but retains the
  hold; the real inventory yields a financial hold; not-evidenced when a retained record lacks
  basis. lint + mypy strict clean.

## Deferred

Propagating deletes to live stores (needs the CRM/customer contexts); a persisted erasure
record / DSAR SLA clock; the incident/rollback failure scenario (SRE phase) — the last DEFERRED
one.
