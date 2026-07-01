"""Per-business LLM budget enforcement gate (pure, infra-free)."""

from __future__ import annotations

import pytest

from ab_gateway.llm_budget import LLMBudgetExceeded, gate_llm_spend


def test_call_within_budget_passes() -> None:
    # spent 40_000 + cost 10_000 = 50_000 <= budget 60_000
    gate_llm_spend("acme", cost_minor=10_000, spent_minor=40_000, budget_minor=60_000)


def test_call_exactly_at_budget_passes() -> None:
    gate_llm_spend("acme", cost_minor=10_000, spent_minor=40_000, budget_minor=50_000)


def test_call_over_budget_is_denied_with_context() -> None:
    with pytest.raises(LLMBudgetExceeded) as exc:
        gate_llm_spend("acme", cost_minor=10_000, spent_minor=45_000, budget_minor=50_000)
    err = exc.value
    assert err.business_id == "acme"
    assert err.spent_minor == 45_000
    assert err.cost_minor == 10_000
    assert err.budget_minor == 50_000
