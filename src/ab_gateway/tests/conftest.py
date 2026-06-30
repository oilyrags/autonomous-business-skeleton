"""Fixtures for gateway integration tests. Skips cleanly when infra is down."""

import socket
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_common import db


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def infra() -> None:
    if not (
        _reachable("localhost", 55432) and _reachable("localhost", 8181) and _reachable("localhost", 19092)
    ):
        pytest.skip("infra not reachable — run `make up` (Postgres 55432, OPA 8181, Redpanda 19092)")
    db.init_db()


@pytest.fixture
def clean_db(infra: None) -> Iterator[None]:
    with db.connect() as conn:
        conn.execute("TRUNCATE decisions")
        conn.execute("TRUNCATE audit_log")
        conn.execute("TRUNCATE revoked_principals")
        conn.execute("TRUNCATE kill_switch")
        conn.commit()
    yield


@pytest.fixture
def gateway_client(infra: None) -> Iterator[TestClient]:
    from ab_gateway.app import app

    with TestClient(app) as client:  # startup runs init_db + ensure_topic
        yield client
