---
status: accepted
---

# AsyncAPI event spec completed + contract-tested against the models

The event backbone has two representations that must agree: the Pydantic models producers construct
(`ab_schemas.events`) and the published contract consumers code against
(`architecture/events.asyncapi.yaml`). Six of the eight event models added over recent slices —
`LedgerEntryPosted`, `ExperimentConcluded`, `BusinessActivated`, `CapitalReallocationRecommended`,
`ModelPromoted`, `ModelEvaluationFailed` — were live in code but **undocumented** in the spec. This
closes that gap and adds contract tests so the two can never drift silently again. Recommendations
P4 (expand AsyncAPI + contract tests).

## Changes

- **Spec completed.** Added the six missing messages (payloads = shared `Envelope` + the event's
  own fields), their channels + `send` operations, and expanded `subjectRef.type` with the subject
  kinds these events actually use (`Business`, `Experiment`, `LedgerTransaction`, `Model`).
- **Contract tests** (`src/ab_schemas/tests/test_asyncapi_contract.py`, pure/infra-free, in the
  normal CI suite), parametrized over every `Envelope` subclass:
  1. **documented** — every event model has an AsyncAPI message (no undocumented event ships);
  2. **field parity** — the model's wire (camelCase) fields exactly equal the documented payload's
     inline properties, both directions (a field added/removed on either side fails);
  3. **required parity** — anything the contract marks `required` is non-optional on the model, so a
     producer cannot omit what consumers rely on.

## Verified

24 contract tests (8 models × 3). A negative check (drop a documented field) confirms the parity
test fails on drift — it is not tautological. Full suite 162 passed, 33 skipped; ruff + mypy strict
clean (80 files).

## Deferred

Validating example payloads in the spec against the models; asserting each producer publishes to the
channel address the spec assigns; generating consumer stubs from the spec.
