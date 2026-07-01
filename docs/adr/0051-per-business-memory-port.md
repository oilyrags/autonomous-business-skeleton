---
status: accepted
---

# Per-business memory store (port + in-memory adapter)

Closes part of the P2 "persistent memory layer (vector DB + knowledge graph) scoped per business"
gap: the **port + a working adapter + the isolation guarantee**. A real vector backend slots in
behind the same interface. PRD 0003; pure.

## Decisions

- **New `ab_memory` context.** `MemoryStore` **port** (`remember` / `recall` / `forget`), every
  method scoped by `business_id` — the isolation boundary. `InMemoryStore` is the default adapter;
  a vector/pgvector/knowledge-graph adapter implements the same interface, replacing only `recall`'s
  implementation (deterministic substring match → embedding search) not the interface.
- **No cross-business leakage** by construction: items are namespaced by `business_id`; `recall`
  never returns another business's memory, and `forget` erases exactly one business's items (useful
  on sunset / DSAR).
- Retrieval is deterministic: most-recent-first, optional content substring filter + limit.

## Verified

6 pure tests (remember→recall; **per-business isolation**; substring filter most-recent-first;
limit; forget erases only that business; unknown business → empty). `make memory` (in CI) shows two
businesses recalling only their own memory. Full suite 226 passed, 36 skipped; ruff + mypy strict
clean (105 files).

## Deferred

A real embedding/vector adapter (pgvector) + knowledge-graph relations behind the port; relevance
ranking; memory summarisation/compaction.
