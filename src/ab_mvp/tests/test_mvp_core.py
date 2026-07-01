"""MVP generation + deploy: a Blueprint becomes a page and goes live via the deployer port (pure)."""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_mvp.core import deploy_mvp, render
from ab_mvp.deployer import StubDeployer


def _blueprint(bid: str = "acme") -> Blueprint:
    return Blueprint(
        business_id=bid,
        name="Acme",
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
        enabled_modules=("waitlist", "checkout"),
    )


def test_render_includes_business_name_and_is_deterministic() -> None:
    a = render(_blueprint())
    b = render(_blueprint())
    assert "Acme" in a.html
    assert a.content_hash == b.content_hash  # same blueprint -> same page/hash


def test_render_differs_when_the_blueprint_differs() -> None:
    a = render(_blueprint("acme"))
    other = _blueprint("beta")
    other = other.model_copy(update={"name": "Beta"})
    b = render(other)
    assert a.content_hash != b.content_hash


def test_deploy_mvp_returns_a_url_and_a_business_scoped_event() -> None:
    deployment, event = deploy_mvp(_blueprint("acme"), StubDeployer())
    assert deployment.url == "https://acme.mvp.stub.local/"
    assert deployment.business_id == "acme"
    assert event.event_name == "MvpDeployed"
    assert event.business_id == "acme"
    assert event.content_hash == deployment.content_hash  # event carries the deployed page's hash
