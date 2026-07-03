"""Console /product workspace (PRD 0008 P3): product initiatives + gated-SDLC status + a per-business
charter theme-swatch preview + human launch/DPIA approval through a governed ProductPort. Infra-free."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_console.auth import sign_identity

_OPERATOR = {
    "X-Operator-Id": "alice.ops",
    "X-Operator-Role": "operator",
    "X-Operator-Sig": sign_identity("alice.ops", "operator"),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    from ab_console.app import app

    with TestClient(app, headers=_OPERATOR) as c:
        yield c
    app.dependency_overrides.clear()


# --- view-model (pure) ---------------------------------------------------------------------------


def test_product_workspace_maps_status_badges_and_a_distinct_theme_swatch() -> None:
    from ab_console.viewmodels import product_workspace
    from ab_product.pipeline import PipelineState, Stage

    states = [
        PipelineState("i1", "alpha", Stage.DPIA, "awaiting_human"),
        PipelineState("i2", "beta", Stage.SCAFFOLD, "halted", "charter conformance failed"),
        PipelineState("i3", "gamma", Stage.LAUNCHED, "launched"),
    ]
    by = {r.initiative_id: r for r in product_workspace(states).rows}

    assert by["i1"].awaiting_human is True and by["i1"].badge == "badge-warning"
    assert by["i2"].badge == "badge-error"
    assert by["i3"].badge == "badge-success"
    assert by["i1"].swatch_primary.startswith("#")  # the business's design-language preview
    assert by["i1"].swatch_primary != by["i2"].swatch_primary  # distinct per business


# --- routes --------------------------------------------------------------------------------------


def test_product_page_lists_initiatives_with_swatches_and_the_advisory_note(client: TestClient) -> None:
    body = client.get("/product").text
    assert "Product" in body and "awaiting_human" in body  # a gated initiative surfaced
    assert "advisory" in body.lower()  # the LLM-proposes note, distinct from deterministic stage badges


def test_product_page_requires_auth() -> None:
    from ab_console.app import app

    with TestClient(app) as anon:
        assert anon.get("/product").status_code == 401


def test_approve_routes_through_the_governed_product_port_with_the_real_operator(client: TestClient) -> None:
    from ab_console.app import app, product_port_provider
    from ab_console.product_port import StubProductPort

    stub = StubProductPort()
    app.dependency_overrides[product_port_provider] = lambda: stub
    resp = client.post("/product/approve", data={"initiative_id": "i1", "stage": "dpia"})
    assert resp.status_code == 200
    assert stub.approvals[0]["initiative_id"] == "i1"
    assert stub.approvals[0]["actor"] == "alice.ops"  # the real, signature-verified operator


def test_a_read_only_role_cannot_approve() -> None:
    from ab_console.app import app

    viewer = {
        "X-Operator-Id": "vic.viewer",
        "X-Operator-Role": "viewer",
        "X-Operator-Sig": sign_identity("vic.viewer", "viewer"),
    }
    with TestClient(app, headers=viewer) as c:
        assert c.post("/product/approve", data={"initiative_id": "i1", "stage": "dpia"}).status_code == 403
