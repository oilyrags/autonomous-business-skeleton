"""HttpKillSwitchPort against the live kill-switch service (integration). Skips fast when the
service isn't up — run `make up-infra` + the killswitch service (docker-compose port 18002)."""

from __future__ import annotations

import socket

import pytest

from ab_console.killswitch_port import HttpKillSwitchPort


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def killswitch_service() -> None:
    if not _reachable("localhost", 18002):
        pytest.skip("kill-switch service not reachable — `docker compose up killswitch` (port 18002)")


def test_console_activation_reaches_the_governed_service(killswitch_service: None) -> None:
    port = HttpKillSwitchPort("http://localhost:18002")
    result = port.activate(
        scope="agent", target_id="console-integration-test", reason="integration drill", activated_by="test"
    )
    assert result.ok is True  # the governed service accepted + persisted + audited it
