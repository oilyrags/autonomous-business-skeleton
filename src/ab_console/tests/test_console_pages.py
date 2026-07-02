"""G2–G5 pages: business detail, experiments, audit explorer, kill switch (TestClient, infra-free)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_console.app import app, killswitch_port_provider
from ab_console.auth import sign_identity
from ab_console.killswitch_port import StubKillSwitchPort

_OPERATOR = {
    "X-Operator-Id": "test.operator",
    "X-Operator-Role": "operator",
    "X-Operator-Sig": sign_identity("test.operator", "operator"),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, headers=_OPERATOR) as c:  # authenticated by default (VULN-001)
        yield c
    app.dependency_overrides.clear()


# --- G2: Business Detail ---------------------------------------------------------------------------


def test_business_detail_shows_economics_checks_and_experiments(client: TestClient) -> None:
    body = client.get("/business/hog").text
    assert "hog" in body and "unprofitable" in body
    assert "-€300.00" in body  # operating loss from minor units
    assert "hog-health" in body  # its monitor check
    assert "exp-price-2" in body  # its experiment
    assert "exp-cta-1" not in body  # rocket's experiment does not leak in


def test_unknown_business_renders_a_calm_404(client: TestClient) -> None:
    resp = client.get("/business/ghost")
    assert resp.status_code == 404
    assert "No business called" in resp.text
    assert "Back to the fleet" in resp.text


# --- G4: Experiments --------------------------------------------------------------------------------


def test_experiments_page_lists_outcomes_with_stats(client: TestClient) -> None:
    body = client.get("/experiments").text
    assert "exp-cta-1" in body and "exp-price-2" in body
    assert "0.0001" in body  # p-value shown
    assert "+8.0%" in body  # lift shown


def test_experiments_filter_by_business(client: TestClient) -> None:
    body = client.get("/experiments?business_id=rocket").text
    assert "exp-cta-1" in body
    assert "exp-price-2" not in body  # hog's experiment filtered out
    assert "filtered to rocket" in body


# --- G5: Audit Explorer -----------------------------------------------------------------------------


def test_audit_explorer_lists_decisions_with_integrity(client: TestClient) -> None:
    body = client.get("/audit").text
    assert "hash chain intact" in body
    assert "dec-001" in body and "dec-002" in body and "dec-003" in body
    assert "L2" in body and "autonomous_within_policy" in body


def test_audit_filters_by_business_and_agent(client: TestClient) -> None:
    body = client.get("/audit?business_id=rocket").text
    assert "dec-001" in body and "dec-002" not in body
    body = client.get("/audit?agent_id=treasury.control_agent").text
    assert "dec-002" in body and "dec-001" not in body


# --- G3: Kill Switch ---------------------------------------------------------------------------------


def test_killswitch_page_shows_deliberate_confirm_ui(client: TestClient) -> None:
    body = client.get("/killswitch").text
    assert "blast radius" in body
    assert "Halts EVERY agent" in body  # global scope explained
    assert "HALT" in body  # the confirm phrase
    assert "Reason (required" in body


def test_activation_requires_a_reason(client: TestClient) -> None:
    resp = client.post("/killswitch", data={"scope": "global", "reason": "", "confirm": "HALT"})
    assert resp.status_code == 400
    assert "A reason is required" in resp.text


def test_activation_requires_the_typed_confirm_phrase(client: TestClient) -> None:
    resp = client.post("/killswitch", data={"scope": "global", "reason": "drill", "confirm": "yes"})
    assert resp.status_code == 400
    assert "Type HALT to confirm" in resp.text


def test_valid_activation_routes_through_the_governed_port(client: TestClient) -> None:
    stub = StubKillSwitchPort()
    app.dependency_overrides[killswitch_port_provider] = lambda: stub
    resp = client.post(
        "/killswitch",
        data={"scope": "agent", "target_id": "executive.cmo_agent", "reason": "anomaly", "confirm": "HALT"},
    )
    assert resp.status_code == 200
    assert "Kill switch activated" in resp.text
    assert stub.activations == [
        {
            "scope": "agent",
            "target_id": "executive.cmo_agent",
            "reason": "anomaly",
            "activated_by": "test.operator",  # real operator identity (VULN-001)
        }
    ]
