"""The ProductBlueprint (PRD 0008 P1b): the typed engineering spec the LLM fills through a port; the
Scaffolder consumes it. A `StubProductModel` proposes a deterministic spec (distinct design tokens
per business) for CI; the real ModelGateway adapter lands in P5 behind the same port.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from ab_product.charter import DesignTokens, default_tokens
from ab_schemas.models import ProductInitiative


class ProductBlueprint(BaseModel):
    """A product's engineering spec: what to build + its proposed design language."""

    business_id: str = Field(min_length=1)
    name: str
    summary: str = ""
    features: list[str] = Field(default_factory=list)
    screens: list[str] = Field(default_factory=list)
    design_tokens: DesignTokens


class ProductModel(Protocol):
    """Propose a ProductBlueprint for an initiative + resolved business_id (the LLM seam)."""

    def spec(self, initiative: ProductInitiative, business_id: str) -> ProductBlueprint: ...


class StubProductModel:
    """A deterministic spec for tests + the demo. The real adapter proposes it via model_gateway (P5)."""

    def spec(self, initiative: ProductInitiative, business_id: str) -> ProductBlueprint:
        return ProductBlueprint(
            business_id=business_id,
            name=initiative.title,
            summary=initiative.hypothesis or f"Product for {initiative.title}.",
            features=list(initiative.key_features),
            screens=["dashboard"],
            design_tokens=default_tokens(business_id),
        )
