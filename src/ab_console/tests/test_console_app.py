"""Fleet Dashboard route: renders the view-model through the design system (TestClient, infra-free)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_console.app import app, fleet_provider
from ab_console.viewmodels import FleetView, fleet


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_dashboard_renders_totals_and_business_rows(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert "Fleet" in body
    assert "rocket" in body and "hog" in body  # business rows
    assert "€16,500.00" in body  # fleet total revenue (1_650_000 minor)
    assert "-€300.00" in body  # hog's operating loss (-30_000 minor)
    assert 'class="pill critical"' in body  # hog's critical health pill
    assert "3 businesses under management" in body


def test_dashboard_serves_the_design_system_stylesheet(client: TestClient) -> None:
    assert '<link rel="stylesheet" href="/static/console.css">' in client.get("/").text
    assert client.get("/static/console.css").status_code == 200


def test_empty_fleet_shows_the_onboarding_state(client: TestClient) -> None:
    app.dependency_overrides[fleet_provider] = lambda: fleet(
        [], anomalies=[], checks=[], kill_switch_active=False
    )
    body = client.get("/").text
    assert "No businesses yet" in body
    assert "<table>" not in body  # the empty state replaces the data table


def test_active_kill_switch_shows_the_banner(client: TestClient) -> None:
    app.dependency_overrides[fleet_provider] = lambda: FleetView(
        businesses=1,
        total_revenue_minor=0,
        total_spend_minor=0,
        total_operating_profit_minor=0,
        unprofitable=0,
        alert_count=0,
        kill_switch_active=True,
        kill_switch_reason="rotation drill",
        rows=[],
    )
    body = client.get("/").text
    assert "Kill switch is ACTIVE" in body and "rotation drill" in body
    assert 'class="pill critical">kill switch active' in body  # top-bar state


def test_render_smoke_exits_zero() -> None:
    from ab_console.__main__ import main

    assert main() == 0  # the `make console` CI smoke: page + stylesheet render end to end
