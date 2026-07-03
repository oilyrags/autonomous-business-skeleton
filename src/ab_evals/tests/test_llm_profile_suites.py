"""The advisory LLM profiles (PRD 0009 S3): `ideation` + `product_spec` must be promotable — a
capable model passes the gate, an injection-leaking model is blocked. Without these suites the real
ideation/product adapters can never be promoted (they abstain forever). Infra-free."""

from __future__ import annotations

import pytest

from ab_evals.gate import evaluate_and_gate
from ab_evals.models import LeakyModel, StubModel
from ab_evals.suites import IDEATION, PRODUCT_SPEC, SUITES


def test_both_llm_profiles_are_registered() -> None:
    assert "ideation" in SUITES and "product_spec" in SUITES  # promotable at all


@pytest.mark.parametrize("suite", [IDEATION, PRODUCT_SPEC])
def test_a_capable_model_is_promoted(suite: object) -> None:
    assert evaluate_and_gate(StubModel(), suite).promoted is True  # type: ignore[arg-type]


@pytest.mark.parametrize("suite", [IDEATION, PRODUCT_SPEC])
def test_a_canary_leaking_model_is_blocked(suite: object) -> None:
    # the safety case is critical — a single injection leak blocks promotion regardless of score
    assert evaluate_and_gate(LeakyModel(), suite).promoted is False  # type: ignore[arg-type]
