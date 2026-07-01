# Business Factory

Instantiates a new business from a Blueprint + capital, behind a readiness gate, and only then clears it to spend.

## Language

**Business**:
An instantiated venture with a Blueprint, allocated capital, and a status (`draft` → `active`).
_Avoid_: company, tenant, venture (informally)

**Readiness Gate**:
The launch check a business must pass to go active: funded, kill-switch clear, and compliance (RoPA) clear.
_Avoid_: approval, validation

**Provision**:
Register a business as draft and allocate its capital as a maker-checker ledger transaction.
_Avoid_: create, set up
