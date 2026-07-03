"""The Scaffolder (PRD 0008 P1b): deterministically emit a business_id-scoped FastAPI + vendored-
daisyUI product service, themed by the BusinessCharter and conformant by construction. Pure."""

from __future__ import annotations

from ab_product.blueprint import StubProductModel
from ab_product.charter import BusinessCharter, charter_conformance
from ab_product.scaffold import scaffold
from ab_schemas.models import ProductInitiative


def _blueprint_and_charter(business_id: str) -> tuple[object, BusinessCharter]:
    init = ProductInitiative(initiative_id="i1", title="Vehicle Twin", key_features=["health score"])
    blueprint = StubProductModel().spec(init, business_id)
    charter = BusinessCharter(business_id=business_id, version=1, tokens=blueprint.design_tokens)
    return blueprint, charter


def test_scaffold_emits_a_themed_business_scoped_conformant_service() -> None:
    blueprint, charter = _blueprint_and_charter("vehicle-twin")
    plan = scaffold(blueprint, charter)  # type: ignore[arg-type]

    assert plan.business_id == "vehicle-twin"  # the service is scoped to the business
    index = next(f for f in plan.files if f.path.endswith("index.html"))
    assert 'data-theme="vehicle-twin"' in index.content  # themed by the charter
    assert "--color-primary" in index.content  # the charter's generated theme is embedded
    assert charter_conformance(plan.artifact, charter).ok is True  # conformant by construction


def test_two_businesses_get_distinctly_themed_scaffolds() -> None:
    plan_a = scaffold(*_blueprint_and_charter("alpha"))  # type: ignore[arg-type]
    plan_b = scaffold(*_blueprint_and_charter("beta"))  # type: ignore[arg-type]
    idx = lambda p: next(f.content for f in p.files if f.path.endswith("index.html"))  # noqa: E731
    assert idx(plan_a) != idx(plan_b)  # distinct design language per business, in the shipped UI
