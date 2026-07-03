"""Persisted promotion (PRD 0009 S2): `record` writes + publishes an audited ModelPromoted, and
`hydrate` loads persisted promotions into the in-memory registry. Infra-free (db + bus faked)."""

from __future__ import annotations

import json
from typing import Any

from ab_evals import promotion_store
from ab_evals.registry import PromotionRegistry


class _Cur:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[tuple[str, str]]:
        return self._rows


class _Conn:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self._rows = rows
        self.executed: list[str] = []

    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *_: Any) -> bool:
        return False

    def execute(self, sql: str, _params: tuple[Any, ...] = ()) -> _Cur:
        self.executed.append(sql)
        return _Cur(self._rows if sql.strip().upper().startswith("SELECT") else [])

    def commit(self) -> None:
        pass


def test_record_persists_and_publishes_model_promoted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    conn = _Conn([])
    published: list[tuple[str, str, Any]] = []
    monkeypatch.setattr(promotion_store.db, "connect", lambda: conn)
    monkeypatch.setattr(
        promotion_store.bus, "publish", lambda topic, key, value: published.append((topic, key, value))
    )

    promotion_store.record("ideation", "stub-v1", eval_score=0.9, decided_by="ops.eval_promote")

    assert any(s.strip().upper().startswith("INSERT INTO MODEL_PROMOTIONS") for s in conn.executed)
    assert len(published) == 1
    _topic, key, value = published[0]
    assert key == "ideation"
    wire = json.loads(value)
    assert wire["eventName"] == "ModelPromoted"
    assert wire["taskProfile"] == "ideation" and wire["modelVersion"] == "stub-v1"


def test_hydrate_loads_persisted_promotions_into_the_registry(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        promotion_store.db, "connect", lambda: _Conn([("ideation", "portkey"), ("product_spec", "portkey")])
    )
    registry = PromotionRegistry()
    assert registry.is_promoted("ideation") is False

    n = promotion_store.hydrate(registry)

    assert n == 2
    assert registry.promoted_version("ideation") == "portkey"
    assert registry.is_promoted("product_spec") is True
