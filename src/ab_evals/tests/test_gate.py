"""Infra-free tests: the eval gate promotes good models and blocks bad ones."""

from ab_evals import __main__ as cli
from ab_evals.gate import evaluate_and_gate
from ab_evals.models import BrokenModel, LeakyModel, StubModel
from ab_evals.suites import EXECUTIVE_REASONING


def test_good_model_is_promoted_and_emits_event() -> None:
    d = evaluate_and_gate(StubModel(), EXECUTIVE_REASONING)
    assert d.promoted is True
    assert d.report.score == 1.0
    assert d.promoted_event is not None and d.failed_event is None
    ev = d.promoted_event
    assert ev.event_name == "ModelPromoted"
    assert ev.task_profile == "executive_reasoning"
    assert ev.model_version == "stub-1.0"
    assert ev.eval_score == 1.0


def test_prompt_injection_leak_is_a_critical_block() -> None:
    d = evaluate_and_gate(LeakyModel(), EXECUTIVE_REASONING)
    assert d.promoted is False
    assert d.failed_event is not None and d.promoted_event is None
    ev = d.failed_event
    assert ev.event_name == "ModelEvaluationFailed"
    assert "safety_no_canary_leak" in ev.failed_cases
    assert "critical" in d.reason  # blocked on the critical safety case, not just score


def test_low_capability_model_is_blocked_on_score() -> None:
    d = evaluate_and_gate(BrokenModel(), EXECUTIVE_REASONING)
    assert d.promoted is False
    ev = d.failed_event
    assert ev is not None
    # BrokenModel returns "" -> fails both capability cases, passes the (non-leak) safety case.
    assert ev.eval_score < EXECUTIVE_REASONING.min_score
    assert "cap_refund_mentions_topic" in ev.failed_cases


def test_cli_gate_passes_for_release_candidate_and_blocks_bad() -> None:
    # Exits 0: the shipped stub passes, and the known-bad candidates are still blocked.
    assert cli.main() == 0
