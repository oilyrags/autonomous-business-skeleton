"""Submit the check suite to a live Icinga2 (integration). Skips fast when the monitoring profile
isn't up — run `docker compose -f docker-compose.monitoring.yml up -d` + set ICINGA2_API_PASSWORD.
"""

from __future__ import annotations

import os
import socket

import pytest

from ab_monitor.icinga2 import Icinga2RestExporter
from ab_monitor.suite import demo_suite


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def icinga2() -> tuple[str, str]:
    if not _reachable("localhost", 5665):
        pytest.skip("Icinga2 not reachable — `docker compose -f docker-compose.monitoring.yml up -d`")
    password = os.environ.get("ICINGA2_API_PASSWORD")
    if not password:
        pytest.skip("ICINGA2_API_PASSWORD not set")
    return os.environ.get("ICINGA2_API_USER", "api"), password


def test_suite_submits_to_live_icinga2(icinga2: tuple[str, str]) -> None:
    user, password = icinga2
    exporter = Icinga2RestExporter("https://localhost:5665", user, password, verify=False)
    exporter.export(demo_suite())  # raises if the REST submit fails
