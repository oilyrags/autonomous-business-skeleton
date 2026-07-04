"""The ideation model route (PRD 0010 M2): GLM-5.2 with a generous reasoning-token budget so the
model doesn't return empty content. Infra-free."""

from __future__ import annotations

from ab_gateway.model_routes import ROUTES


def test_ideation_routes_to_glm_5_2_with_a_generous_token_budget() -> None:
    route = ROUTES["ideation"]
    assert route.model == "z-ai/glm-5.2"  # GLM-5.2 via OpenRouter slug
    assert int(route.params["max_tokens"]) >= 4096  # reasoning models need room to "think"
