---
status: accepted
---

# Living Playbooks — pattern extraction into versioned blueprints

Closes the P1/P5 "Living Playbooks — extract successful strategies from winning businesses into
versioned, reusable blueprints" gap + "cross-business what-works pattern detection (with privacy)".
PRD 0003; pure, deterministic.

## Decisions

- **New `ab_playbook` context.** `extract_playbook(winners, *, version) -> Playbook` distils the
  blueprints of winning businesses: **median** economics (target revenue, experiment budget,
  min conversion rate, max CAC) and the modules a **strict majority** of winners enabled
  (frequency-ranked, deterministic).
- **Privacy-preserving by construction**: a `Playbook` carries only aggregates — median economics +
  module frequency counts + sample size — and has **no `business_id` field**, so a winning strategy
  transfers without leaking any one business's detail.
- **The reuse half**: `apply_playbook(playbook, *, business_id, name) -> Blueprint` instantiates a
  brand-new business's Blueprint from the distilled playbook — closing the learn → reuse loop.

## Verified

5 pure tests (median economics; majority modules; aggregate-only / no business_id; apply
instantiates a blueprint; empty-winners raises). `make playbook` (in CI) distils three winners and
instantiates `newco`. Full suite 220 passed, 36 skipped; ruff + mypy strict clean (102 files).

## Deferred

Selecting winners from live `ExperimentConcluded`/portfolio outcomes (rather than passed-in
blueprints); versioned playbook storage + provenance; a blueprint marketplace (P5).
