---
status: accepted
---

# Compliance lawful-basis CI gate — Audit 4

The `08` data inventory (RoPA, GDPR Art.30) states: *"Every personal-data element MUST have
an entry. CI fails if a `personal`-classified event/field has no matching record."* This
slice implements that gate, closing verification Audit 4.

## Decisions

- **`ab_compliance` (Compliance context).** `ropa.check()` cross-checks three sources against
  the `08` RoPA and returns a list of violations (empty == compliant):
  - **RoPA integrity** — every `08` record classified `personal`/`financial` has a
    `lawfulBasis`; every record has a `retentionPolicy` that resolves in `retentionPolicies`;
    no duplicate `dataElement`s.
  - **Code inventory** (`ab_data.inventory.DATA_INVENTORY`) — every element's retention
    resolves, and any `personal`/`financial` element has an `08` RoPA record. This is the part
    that guards the running system: add a personal field in code without documenting it → CI
    fails.
  - **Event catalog** (`04`) — every `personal` event has a lawful basis, either declared
    inline or (per Art.30) documented at the RoPA level via an `08` record for the event's
    retention policy; every sensitive event's retention resolves.
- **Basis can live in the RoPA, not just inline.** DSAR-fulfilment events
  (`DataExportCompleted`, `RectificationCompleted`, …) are `personal` under
  `legal_obligation`, documented once on the `dsar.subject_identity` record — the gate links
  event → RoPA record via retention policy rather than demanding each event restate its basis.
- **`make compliance`** runs the gate (pure, no infra) and is in the CI `check` job; a
  non-empty violation list exits non-zero.

## Verified

- `make compliance` → PASS on the shipped artifacts. Tests (+7): real artifacts compliant;
  and each violation type is caught by failure-injection — a personal `08` record with no
  lawful basis; an undefined retention policy; a personal code-inventory element with no RoPA
  record; a personal event with no inline **and** no RoPA-linked basis; plus the positive
  linked-basis case. lint + mypy strict clean.

## Audit impact

**Audit 4 (compliance) → PASS (build-proven).** `architecture/16` updated; CONDITIONAL 2 → 1
(only Audit 12, failure-injection suite, remains).

## Deferred

Parsing `07_data_model.md` fields (currently the code inventory + `04` events are the checked
surfaces); per-record DSAR routing assertions; asserting classification consistency between
`ab_schemas` events and the RoPA; consent-state enforcement at runtime.
