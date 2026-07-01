---
status: accepted
---

# business_id on the decision path

Completes the P4 "propagate business_id as a first-class concern" work: after the money path
(ADR-0038), the *decision* path now carries `business_id` too, so every material decision is
attributable to a business. PRD 0003; the ADR-0037 contract test drove the event change.

## Changes

- **`AgentDecisionMade.business_id: str | None`** (optional — platform/cross-business decisions have
  none). Adding it failed AsyncAPI field-parity until the payload gained an optional `businessId`.
- **`decisions.business_id` column** (nullable, in the `IF NOT EXISTS` DDL); `write_decision`
  persists it; `DecisionWrite` gains the optional field.
- **Gateway emission** sets `business_id` on the published `AgentDecisionMade` from the tool args.

## Verified

2 pure tests (defaults None; round-trips as camelCase `businessId`); AsyncAPI contract green; the
existing gateway decision integration tests still pass (business_id defaults None when unset). Full
suite 209 passed, 36 skipped; ruff + mypy strict clean (96 files).

## Deferred

business_id on the audit-log rows; back-linking a decision to the business event that prompted it.
