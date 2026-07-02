"""Console v0.2: sparklines, live SSE feed, decision workspace (infra-free)."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_console.app import app, approval_port_provider
from ab_console.approvals import StubApprovalPort
from ab_console.auth import sign_identity
from ab_console.viewmodels import PendingDecision, decisions_view, sparkline_points

_OPERATOR = {
    "X-Operator-Id": "alice.ops",
    "X-Operator-Role": "operator",
    "X-Operator-Sig": sign_identity("alice.ops", "operator"),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, headers=_OPERATOR) as c:  # authenticated by default (VULN-001)
        yield c
    app.dependency_overrides.clear()


# --- Sparklines --------------------------------------------------------------------------------------


def test_sparkline_normalizes_to_the_value_range() -> None:
    # Two points, width 120 / height 28 / pad 2: min sits at the bottom, max at the top.
    assert sparkline_points([0, 10]) == "2.0,26.0 118.0,2.0"


def test_sparkline_flat_series_draws_a_line_not_a_crash() -> None:
    assert sparkline_points([5, 5, 5]) == "2.0,26.0 60.0,26.0 118.0,26.0"  # span 0 -> bottom line


def test_sparkline_needs_two_points() -> None:
    assert sparkline_points([7]) == "" and sparkline_points([]) == ""


def test_fleet_rows_render_sparklines(client: TestClient) -> None:
    body = client.get("/").text
    assert "<polyline" in body
    assert 'aria-label="profit trend for rocket"' in body


# --- Live feed (SSE) ----------------------------------------------------------------------------------


def test_event_stream_is_sse_with_decision_events(client: TestClient) -> None:
    resp = client.get("/events/stream")
    assert resp.headers["content-type"].startswith("text/event-stream")
    frames = [line for line in resp.text.split("\n\n") if line.startswith("data: ")]
    assert len(frames) == 5  # the stub's sample events
    first = json.loads(frames[0].removeprefix("data: "))
    assert first["eventName"] == "AgentDecisionMade" and first["businessId"] == "rocket"


def test_feed_page_uses_native_eventsource(client: TestClient) -> None:
    body = client.get("/feed").text
    assert 'new EventSource("/events/stream")' in body
    assert "Live feed" in body


# --- Decision workspace --------------------------------------------------------------------------------


def test_decisions_view_orders_by_authority_desc() -> None:
    a = PendingDecision("d1", "payment", "s", 1, "m", 4, None)
    b = PendingDecision("d2", "reallocation", "s", 1, "m", 5, None)
    assert [d.decision_id for d in decisions_view([a, b]).pending] == ["d2", "d1"]  # L5 first


def test_decisions_page_shows_the_queue(client: TestClient) -> None:
    body = client.get("/decisions").text
    assert "Pay supplier invoice over the cap" in body
    assert "Sunset &#39;sinker&#39;" in body or "Sunset 'sinker'" in body
    assert "L5" in body and "L4" in body
    assert "€1,500.00" in body  # 150_000 minor formatted


def test_approve_routes_through_the_governed_port_and_clears_the_item(client: TestClient) -> None:
    stub = StubApprovalPort()
    app.dependency_overrides[approval_port_provider] = lambda: stub
    resp = client.post(
        "/decisions/act", data={"decision_id": "pend-201", "action": "approve", "note": "checked evidence"}
    )
    assert resp.status_code == 200
    assert "approved pend-201" in resp.text
    assert "Pay supplier invoice" not in resp.text  # cleared from the queue
    assert stub.actions == [
        {
            "action": "approve",
            "decision_id": "pend-201",
            "actor": "alice.ops",  # the real, signature-verified operator — not a constant (VULN-001)
            "note": "checked evidence",
        }
    ]


def test_a_read_only_role_cannot_approve() -> None:
    viewer = {
        "X-Operator-Id": "vic.viewer",
        "X-Operator-Role": "viewer",  # not a mutating role
        "X-Operator-Sig": sign_identity("vic.viewer", "viewer"),
    }
    with TestClient(app, headers=viewer) as c:
        resp = c.post("/decisions/act", data={"decision_id": "pend-201", "action": "approve"})
    assert resp.status_code == 403


def test_cross_origin_write_is_refused() -> None:
    resp = None
    with TestClient(app, headers={**_OPERATOR, "Origin": "https://evil.example", "Host": "console"}) as c:
        resp = c.post("/decisions/act", data={"decision_id": "pend-201", "action": "approve"})
    assert resp.status_code == 403


def test_killswitch_records_the_real_operator_not_a_constant() -> None:
    from ab_console.app import killswitch_port_provider
    from ab_console.killswitch_port import StubKillSwitchPort

    stub = StubKillSwitchPort()
    app.dependency_overrides[killswitch_port_provider] = lambda: stub
    with TestClient(app, headers=_OPERATOR) as c:
        resp = c.post("/killswitch", data={"scope": "global", "reason": "drill", "confirm": "HALT"})
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert stub.activations[0]["activated_by"] == "alice.ops"


def test_reject_requires_a_note(client: TestClient) -> None:
    resp = client.post("/decisions/act", data={"decision_id": "pend-201", "action": "reject", "note": ""})
    assert resp.status_code == 400
    assert "A note is required to reject" in resp.text


def test_unknown_decision_or_action_is_a_400(client: TestClient) -> None:
    assert client.post("/decisions/act", data={"decision_id": "nope", "action": "approve"}).status_code == 400
    assert (
        client.post("/decisions/act", data={"decision_id": "pend-201", "action": "explode"}).status_code
        == 400
    )


def test_metrics_endpoint_serves_prometheus_gauges(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain; version=0.0.4")
    body = resp.text
    assert 'ab_check_status{check="hog-health",business_id="hog"} 2' in body  # CRITICAL
    assert 'ab_business_operating_profit_minor{business_id="hog"} -30000' in body
    assert "ab_fleet_businesses 3" in body
