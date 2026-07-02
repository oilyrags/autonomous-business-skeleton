# G5 — Audit & Decision Explorer

**Parent:** PRD 0006 / ADR-0056.

## What to build
A searchable, filterable view of agent decisions, human overrides, and system events, deep-linked
and tamper-evident. `viewmodels.audit(...)` (pure) shapes decision/audit rows (decision id, agent,
authority level, approval status, business_id, timestamp) with filters (business/agent/type/time).
`GET /audit` renders the explorer; a hash-chain-intact indicator conveys tamper-evidence. Deep link
from a decision to its linked event.

## Acceptance criteria
- [ ] `audit(...)` pure, returns filtered rows + the integrity indicator; unit-tested (filters).
- [ ] `GET /audit` 200 with filters applied via query params; tested via TestClient.
- [ ] Tamper-evident state shown; rows deep-link; accessible table semantics. ruff + mypy clean.

## Blocked by
- G1.
