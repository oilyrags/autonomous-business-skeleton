"""classify: a promoted initiative becomes a NEW business (mint a business_id) or an EXTENSION of an
existing one — deterministically, never an LLM decision (PRD 0008 P1b). Pure, infra-free."""

from __future__ import annotations

from ab_product.classify import classify
from ab_schemas.models import ProductInitiative


def test_an_initiative_without_an_existing_business_is_a_new_business() -> None:
    init = ProductInitiative(
        initiative_id="init-1", title="Verifiable AI Vehicle Twin", key_features=["twin"]
    )
    result = classify(init)
    assert result.kind == "new"
    assert result.business_id == "verifiable-ai-vehicle-twin"  # slug minted from the title
    assert "new business" in result.rationale.lower()


def test_an_initiative_with_an_existing_business_is_an_extension() -> None:
    init = ProductInitiative(
        initiative_id="init-2", title="Faster triage", business_id="inboxiq", key_features=["x"]
    )
    result = classify(init)
    assert result.kind == "extension" and result.business_id == "inboxiq"
