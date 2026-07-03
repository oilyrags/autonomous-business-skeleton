"""Idempotent persist-and-emit — the single place the "publish a domain event exactly when the write
changed a row" invariant lives (architecture-review deepening #3). Composes `db` + `bus`.

Every context's write path repeated the same shape: run an idempotent write (an
``INSERT ... ON CONFLICT DO NOTHING`` or an ``UPDATE`` guarded so it only touches a changed row),
commit, then publish an event **only if a row actually changed** — the invariant that, when it
drifted, produced the double-publish bug in `ab_product.store.save`. This helper owns it once.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ab_schemas.events import Envelope

from . import bus, db


def persist_and_emit(
    sql: str,
    params: tuple[Any, ...],
    *,
    topic: str,
    key: str,
    event: Callable[[], Envelope],
) -> bool:
    """Run an idempotent write, commit, and publish ``event()`` **iff a row changed** (``rowcount ==
    1`` — psycopg reports 1 on an insert / a guarded update, 0 on an ``ON CONFLICT DO NOTHING`` or a
    no-op update). ``event`` is a thunk, built only when it will be published. A replay of the same
    write, or a write of an unknown/unchanged row, is a no-op that emits nothing. Returns True iff a
    row changed."""
    with db.connect() as conn:
        changed = conn.execute(sql, params).rowcount == 1
        conn.commit()
    if changed:
        bus.publish_event(topic, key, event())
    return changed
