"""Per-business memory: scoped recall with no cross-business leakage (pure, infra-free)."""

from __future__ import annotations

from ab_memory.core import InMemoryStore, MemoryItem


def _item(bid: str, key: str, content: str) -> MemoryItem:
    return MemoryItem(business_id=bid, key=key, content=content)


def test_remember_then_recall_returns_the_items() -> None:
    store = InMemoryStore()
    store.remember(_item("acme", "k1", "landing page A converted best"))
    recalled = store.recall("acme")
    assert len(recalled) == 1 and recalled[0].content == "landing page A converted best"


def test_recall_is_isolated_per_business() -> None:
    store = InMemoryStore()
    store.remember(_item("acme", "k1", "acme secret strategy"))
    store.remember(_item("beta", "k1", "beta secret strategy"))
    acme = store.recall("acme")
    assert [i.business_id for i in acme] == ["acme"]  # never sees beta's memory
    assert all("beta" not in i.content for i in acme)


def test_recall_filters_by_content_substring_most_recent_first() -> None:
    store = InMemoryStore()
    store.remember(_item("acme", "k1", "cac is 3000"))
    store.remember(_item("acme", "k2", "conversion rate 0.05"))
    store.remember(_item("acme", "k3", "cac dropped to 2500"))
    cac = store.recall("acme", contains="cac")
    assert [i.key for i in cac] == ["k3", "k1"]  # most-recent first, only cac items


def test_recall_limit_caps_results() -> None:
    store = InMemoryStore()
    for n in range(5):
        store.remember(_item("acme", f"k{n}", f"note {n}"))
    assert len(store.recall("acme", limit=2)) == 2


def test_forget_erases_only_that_business() -> None:
    store = InMemoryStore()
    store.remember(_item("acme", "k1", "x"))
    store.remember(_item("beta", "k1", "y"))
    store.forget("acme")
    assert store.recall("acme") == []
    assert len(store.recall("beta")) == 1  # beta untouched


def test_recall_unknown_business_is_empty() -> None:
    assert InMemoryStore().recall("ghost") == []
