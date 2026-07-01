---
status: accepted
---

# Policy-enforcement property tests

Closes the P4 "property-based testing for … policy enforcement" gap (the ledger/allocator money
invariants were done in ADR-0036). The money-authority policy — maker-checker + separation of duties
+ the payee allow-list — is now proven for arbitrary payments, not just hand-picked cases. PRD 0003.

## Invariants pinned (Hypothesis, pure)

For arbitrary outbound payments (payee approved-or-not, amount under/over the cap, checker
none/maker/distinct):
- A payment over the cap **or** to an off-allow-list payee **requires approval**: no checker →
  `ApprovalRequired`; checker == maker → `SeparationOfDutiesViolation`; a distinct checker → posts.
- An approved payee at/under the cap **never** requires approval — posts with or without a checker.
- Over the cap is **always** gated, even for an approved payee.

## Verified

3 property tests (`src/ab_ledger/tests/test_policy_properties.py`), infra-free, in the normal CI
suite. Full suite 212 passed, 36 skipped; ruff + mypy strict clean.

## Deferred

Property tests over the OPA authority policy + the L0–L5 autonomy matrix (needs the OPA sidecar or a
local rego evaluator).
