# Memory

Per-business agent memory: a store namespaced by business_id so an agent recalls its own prior
context with no cross-business leakage. A real vector/knowledge-graph backend slots in behind the port.

## Language

**Memory Item**:
A stored piece of an agent's context (business_id, key, content) — the unit written and recalled.
_Avoid_: note, record, embedding (an embedding is the vector backend's artifact)

**Scoped Recall**:
Retrieval restricted to one business_id; recall never crosses the isolation boundary.
_Avoid_: search, lookup, query (when you mean the isolated retrieval)

**Forget**:
Erasing exactly one business's memory (e.g. on sunset or DSAR), leaving others untouched.
_Avoid_: delete, clear, purge
