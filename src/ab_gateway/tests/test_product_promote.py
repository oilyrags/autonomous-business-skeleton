"""product.initiative.promote (PRD 0008 P1b): the governed spine — promote → classify → blueprint →
scaffold → charter-conformance gate → ProductScaffolded. Infra-free (bus.publish stubbed)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ab_gateway import tools
from ab_schemas.models import ProductInitiative

AGENT = "product.engineering_agent"


def _new_business_args() -> dict[str, object]:
    return ProductInitiative(
        initiative_id="init-1", title="Verifiable AI Vehicle Twin", key_features=["health score"]
    ).model_dump()


def test_promote_rejects_invalid_args_as_a_400() -> None:
    with pytest.raises(tools.ToolDenied) as exc:
        tools.promote_initiative(AGENT, {"initiative_id": "x"})  # missing title
    assert exc.value.status == 400


def test_promote_denies_an_extension_of_a_business_the_principal_does_not_serve() -> None:
    args = ProductInitiative(
        initiative_id="init-2", title="add feature", business_id="rocket", key_features=["x"]
    ).model_dump()
    with pytest.raises(tools.ToolDenied) as exc:
        tools.promote_initiative("mallory.agent", args)  # unknown principal, no tenant grant
    assert exc.value.status == 403


def test_promote_scaffolds_a_new_business_and_emits_once(monkeypatch: pytest.MonkeyPatch) -> None:
    published: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "ab_gateway.tools.bus.publish",
        lambda topic, *, key, value: published.append((topic, key)),
    )
    product_id = tools.promote_initiative(AGENT, _new_business_args())

    assert product_id == "prod_verifiable-ai-vehicle-twin"  # business_id minted from the title
    assert len(published) == 1  # ProductScaffolded emitted exactly once, after the conformance gate


def test_promote_refuses_a_non_conformant_scaffold_before_emitting(monkeypatch: pytest.MonkeyPatch) -> None:
    from ab_product.charter import Artifact
    from ab_product.scaffold import ScaffoldPlan

    published: list[object] = []
    monkeypatch.setattr("ab_gateway.tools.bus.publish", lambda *a, **k: published.append(1))
    # Force the scaffold to declare a forbidden dependency → the conformance gate must reject it.
    bad = ScaffoldPlan(
        business_id="verifiable-ai-vehicle-twin",
        service_name="venture_x",
        files=(),
        artifact=Artifact(
            theme_name="verifiable-ai-vehicle-twin",
            dependencies=frozenset({"requests"}),  # not in the charter's allowed set
            architecture_rules=frozenset(
                {"business_id_tenancy", "ports_and_stubs", "single_governed_ingress"}
            ),
            charter_version=1,
        ),
    )
    monkeypatch.setattr("ab_product.scaffold.scaffold", lambda *a, **k: bad)

    with pytest.raises(tools.ToolDenied) as exc:
        tools.promote_initiative(AGENT, _new_business_args())
    assert "not charter-conformant" in exc.value.reason
    assert published == []  # nothing emitted — the gate ran before any side effect


def test_promote_is_registered_with_a_governed_contract() -> None:
    spec = tools.get("product.initiative.promote")
    assert spec is not None and spec.sensitive is True and spec.side_effect == "write"


def test_initiative_model_requires_a_title() -> None:
    with pytest.raises(ValidationError):
        ProductInitiative(initiative_id="x", title="")
