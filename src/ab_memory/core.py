"""Per-business agent memory (deterministic): a namespaced store so an agent recalls prior context
scoped to *its* business, with **no cross-business leakage**. The store is a port (`MemoryStore`);
the in-memory adapter here is the default, and a vector/knowledge-graph backend slots in behind the
same interface. Retrieval is a simple deterministic substring match — an embedding backend replaces
only the ``recall`` implementation, not the interface.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class MemoryItem(BaseModel):
    business_id: str
    key: str
    content: str


class MemoryStore(Protocol):
    """Scoped agent memory. Every method takes a ``business_id`` — the isolation boundary."""

    def remember(self, item: MemoryItem) -> None: ...
    def recall(
        self, business_id: str, *, contains: str | None = None, limit: int | None = None
    ) -> list[MemoryItem]: ...
    def forget(self, business_id: str) -> None: ...


class InMemoryStore:
    """Deterministic per-business memory for tests + the demo. Items are namespaced by
    ``business_id``; ``recall`` never crosses that boundary. A real vector/pgvector adapter
    implements the same ``MemoryStore`` interface."""

    def __init__(self) -> None:
        self._by_business: dict[str, list[MemoryItem]] = {}

    def remember(self, item: MemoryItem) -> None:
        self._by_business.setdefault(item.business_id, []).append(item)

    def recall(
        self, business_id: str, *, contains: str | None = None, limit: int | None = None
    ) -> list[MemoryItem]:
        """This business's items, most-recent first, optionally filtered by a substring of content."""
        items = list(reversed(self._by_business.get(business_id, [])))
        if contains is not None:
            items = [i for i in items if contains in i.content]
        return items[:limit] if limit is not None else items

    def forget(self, business_id: str) -> None:
        """Erase one business's memory (e.g. on sunset / DSAR) — leaves other businesses untouched."""
        self._by_business.pop(business_id, None)
