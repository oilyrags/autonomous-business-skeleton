"""Audit-9 criteria 2 & 3: grounding-threshold and Art.22 bias gating."""

from ab_evals.gate import evaluate_and_gate, gate
from ab_evals.harness import EvalCase, EvalSet, evaluate
from ab_evals.models import BiasedModel, CompliantModel, HallucinatingModel
from ab_evals.suites import SIGNIFICANT_CUSTOMER_DECISION


def test_compliant_model_passes_grounding_and_bias() -> None:
    d = evaluate_and_gate(CompliantModel(), SIGNIFICANT_CUSTOMER_DECISION)
    assert d.promoted is True
    assert d.report.dimension_score("grounding") == 1.0
    assert d.report.dimension_score("bias") == 1.0


def test_hallucinating_model_blocked_by_grounding_threshold() -> None:
    d = evaluate_and_gate(HallucinatingModel(), SIGNIFICANT_CUSTOMER_DECISION)
    assert d.promoted is False
    assert d.report.dimension_score("grounding") < 1.0
    assert "grounding" in d.reason
    assert d.failed_event is not None
    assert "ground_abstain_unsupported" in d.failed_event.failed_cases


def test_biased_model_blocked_by_bias_threshold_but_grounding_ok() -> None:
    d = evaluate_and_gate(BiasedModel(), SIGNIFICANT_CUSTOMER_DECISION)
    assert d.promoted is False
    assert d.report.dimension_score("grounding") == 1.0  # block is attributable to bias only
    assert "bias" in d.reason
    assert d.failed_event is not None
    assert "bias_decision_invariant_to_group" in d.failed_event.failed_cases


def test_art22_profile_without_bias_eval_is_rejected() -> None:
    # An Art.22 profile that forgot its fairness eval must not be promotable.
    misconfigured = EvalSet(
        task_profile="art22_missing_bias",
        min_score=0.0,
        art22_significant=True,
        cases=(EvalCase(id="cap", dimension="capability", prompt="x", check=lambda o: True),),
    )
    d = gate(evaluate(CompliantModel(), misconfigured), 0.0, art22_significant=True)
    assert d.promoted is False
    assert "Art.22" in d.reason


def test_grounding_threshold_is_enforced_independently_of_overall_score() -> None:
    # Even with a passing overall score, a sub-threshold grounding dimension blocks.
    d = evaluate_and_gate(HallucinatingModel(), SIGNIFICANT_CUSTOMER_DECISION)
    # HallucinatingModel gets the fairness case right (constant APPROVE) yet is still blocked.
    assert d.report.dimension_score("bias") == 1.0
    assert d.promoted is False
