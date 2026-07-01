---
status: accepted
---

# Hierarchical agent teams + charters + escalation

Closes part of the P2 "hierarchical agent teams with clear charters and escalation paths" gap: the
deterministic org model + authority-based routing. Ties to the existing L0–L5 autonomy matrix. PRD
0003; pure.

## Decisions

- **New `ab_org` context.** A `Charter` gives each agent a role, an `authority_level` (0–5, the
  autonomy matrix), a department, and a `reports_to` link. An `Org` is the set of charters.
- **`route(org, *, initiator, required_level) -> Routing`** walks up `reports_to` from the initiator
  to the first agent whose authority covers the decision; if the chain is exhausted, it **escalates
  to a human** — so an L5 (money/high-risk) action, which no agent may take autonomously, always
  reaches a person. Deterministic and cycle-safe; returns the full traversal path.
- **`team(org, department)`** lists a department's charters most-senior first.

## Verified

4 pure tests (agent decides within its level; escalates up to a senior agent; L5 with no L5 agent →
human, whole chain walked; team ordering). `make org` (in CI) routes L1/L3/L5 decisions from an
intern (intern → cmo → ceo → HUMAN for L5). Full suite 230 passed, 36 skipped; ruff + mypy strict
clean (108 files).

## Deferred

Binding routing into the live gateway (so a real tool call escalates via the org); shared team
memory (via `ab_memory`); charter versioning + delegation.
