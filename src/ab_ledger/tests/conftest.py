"""Fixture for ledger persistence tests. Skips cleanly when Postgres is down."""

import socket
from collections.abc import Iterator

import pytest

from ab_common import db


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def pg() -> Iterator[None]:
    if not _reachable("localhost", 55432):
        pytest.skip("Postgres not reachable — run `make up-infra` (PG 55432)")
    db.init_db()
    with db.connect() as conn:
        conn.execute("TRUNCATE ledger_entries, ledger_txns")
        conn.commit()
    yield
