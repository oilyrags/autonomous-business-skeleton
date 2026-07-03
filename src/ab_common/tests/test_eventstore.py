"""`persist_and_emit` publishes a domain event exactly when the write changed a row — the idempotent
persist-and-emit invariant (deepening #3). Infra-free: the db connection + bus are faked."""

from __future__ import annotations

from typing import Any

from ab_common import eventstore
from ab_schemas.events import BusinessActivated, build


class _FakeCursor:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _FakeConn:
    def __init__(self, rowcount: int) -> None:
        self._rowcount = rowcount
        self.committed = False

    def __enter__(self) -> _FakeConn:
        return self

    def __exit__(self, *_: Any) -> bool:
        return False

    def execute(self, _sql: str, _params: tuple[Any, ...]) -> _FakeCursor:
        return _FakeCursor(self._rowcount)

    def commit(self) -> None:
        self.committed = True


def _event() -> BusinessActivated:
    return build(BusinessActivated, subject=("Business", "b"), producer="p",
                 business_id="b", name="B", capital_minor=1)


def _run(monkeypatch, rowcount: int) -> tuple[bool, list[Any], list[int]]:  # type: ignore[no-untyped-def]
    published: list[Any] = []
    built: list[int] = []
    monkeypatch.setattr(eventstore.db, "connect", lambda: _FakeConn(rowcount))
    monkeypatch.setattr(eventstore.bus, "publish_event", lambda t, k, e: published.append((t, k, e)))

    def thunk() -> BusinessActivated:
        built.append(1)
        return _event()

    result = eventstore.persist_and_emit("UPDATE …", (), topic="t", key="k", event=thunk)
    return result, published, built


def test_publishes_and_returns_true_when_a_row_changed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result, published, built = _run(monkeypatch, rowcount=1)
    assert result is True
    assert len(published) == 1  # event emitted on a real transition
    assert len(built) == 1


def test_is_a_silent_noop_when_no_row_changed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result, published, built = _run(monkeypatch, rowcount=0)
    assert result is False
    assert published == []  # no duplicate/no-op event
    assert built == []  # the event thunk is not even built when nothing changed
