"""Console 'Start a business' seed (fix: growth testing needs a business to exist). An operator seeds
a launch-ready business from the fleet dashboard; ab_factory.store.provision governs it. Infra-free."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from ab_console.auth import sign_identity
from ab_console.viewmodels import build_blueprint_seed

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


def test_build_blueprint_seed_from_form() -> None:
    bp, capital = build_blueprint_seed({"business_id": "acme-co", "name": "Acme", "capital_minor": "500000"})
    assert bp.business_id == "acme-co" and bp.name == "Acme" and capital == 500_000
    assert bp.experiment_budget_minor > 0  # a launch-ready-capable blueprint


def test_build_blueprint_seed_requires_a_business_id() -> None:
    with pytest.raises(ValueError, match="business id is required"):
        build_blueprint_seed({"business_id": "  ", "capital_minor": "1000"})


# --- endpoint --------------------------------------------------------------------------------------


def test_the_fleet_page_offers_a_start_a_business_form(client: TestClient) -> None:
    body = client.get("/").text
    assert 'action="/businesses/seed"' in body  # a business can be started from the UI


def test_seeding_provisions_and_confirms(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_factory import store as factory_store

    active = SimpleNamespace(business_id="acme-co", status=SimpleNamespace(value="active"))
    monkeypatch.setattr(factory_store, "provision", lambda bp, capital_minor: active)
    resp = client.post("/businesses/seed", data={"business_id": "acme-co", "capital_minor": "2000000"})
    assert resp.status_code == 200
    assert "Business seeded" in resp.text and "acme-co" in resp.text


def test_seeding_an_empty_id_is_a_400_with_a_message(client: TestClient) -> None:
    resp = client.post("/businesses/seed", data={"business_id": ""})
    assert resp.status_code == 400
    assert "business id is required" in resp.text


def test_seeding_a_duplicate_is_a_409(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_factory import store as factory_store

    def _raise(bp: object, capital_minor: int) -> None:
        raise factory_store.AlreadyProvisioned("acme-co")

    monkeypatch.setattr(factory_store, "provision", _raise)
    resp = client.post("/businesses/seed", data={"business_id": "acme-co"})
    assert resp.status_code == 409 and "already exists" in resp.text
