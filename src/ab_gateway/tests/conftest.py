"""Fixtures for gateway integration tests. Skips cleanly when infra is down."""

import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from ab_common import db
from ab_common.config import settings
from ab_identity.oidc import fetch_token

# Dev client secrets from config/keycloak/ab-realm.json.
_CLIENT_SECRETS = {
    "executive.cmo_agent": "cmo-secret",
    "executive.intern_agent": "intern-secret",
}


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _keycloak_ready(timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(settings.oidc_jwks_url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    return False


@pytest.fixture(scope="session")
def infra() -> None:
    if not (
        _reachable("localhost", 55432) and _reachable("localhost", 8181) and _reachable("localhost", 19092)
    ):
        pytest.skip("infra not reachable — run `make up-infra` (Postgres 55432, OPA 8181, Redpanda 19092)")
    if not _keycloak_ready():
        pytest.skip("Keycloak not ready — run `make up-infra` and wait for realm 'ab'")
    db.init_db()


@pytest.fixture
def make_token(infra: None) -> Callable[[str], str]:
    def _token(agent_id: str) -> str:
        return fetch_token(agent_id, _CLIENT_SECRETS[agent_id])

    return _token


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
