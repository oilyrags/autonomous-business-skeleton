"""The real ProductModel adapter (PRD 0008 P5): proposes the blueprint via model_gateway, but
degrades SAFELY — without an eval-gated model (the default) or on malformed output it returns the
deterministic default blueprint, never a fabricated spec. Infra-free."""

from __future__ import annotations

from ab_product.blueprint import ModelGatewayProductModel, StubProductModel
from ab_schemas.models import ProductInitiative


def test_real_model_falls_back_to_the_deterministic_default_without_a_promoted_model() -> None:
    init = ProductInitiative(initiative_id="i1", title="Vehicle Twin", key_features=["health score"])
    real = ModelGatewayProductModel().spec(init, "vehicle-twin")
    default = StubProductModel().spec(init, "vehicle-twin")
    assert real == default  # model_gateway abstains → the deterministic default, not a fabrication


def test_product_demo_runs_the_spine_to_a_conformant_launched_deployed_product() -> None:
    from ab_product.product_demo import run

    summary = run(verbose=False)
    assert summary.classification == "new"  # a new business is minted
    assert summary.conformant is True  # the scaffold passes the charter gate
    assert summary.launched is True  # the gated SDLC reaches launched (human gates approved)
    assert summary.deployed_url.startswith("http://")  # deployed into the mesh


def test_product_demo_cli_exits_zero() -> None:
    from ab_product.product_demo import main

    assert main() == 0
