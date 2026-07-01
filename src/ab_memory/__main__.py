"""Per-business memory demo (deterministic, no infra).

    uv run python -m ab_memory

Two businesses write to the same store; each recalls only its own memory. A real vector/knowledge-
graph backend slots in behind the same MemoryStore port.
"""

from __future__ import annotations

from ab_memory.core import InMemoryStore, MemoryItem


def main() -> int:
    store = InMemoryStore()
    store.remember(MemoryItem(business_id="rocket", key="e1", content="cac dropped to 2500 on meta"))
    store.remember(MemoryItem(business_id="rocket", key="e2", content="checkout module lifted conversion"))
    store.remember(MemoryItem(business_id="steady", key="e1", content="referral loop worked best"))

    for bid in ("rocket", "steady"):
        recalled = store.recall(bid)
        print(f"  {bid:7} recalls {len(recalled)} item(s):")
        for item in recalled:
            print(f"    - {item.content}")
    print("\n  isolation: rocket cannot see steady's memory (namespaced by business_id)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
