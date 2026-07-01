"""Reliability controls: error budget, release freeze, auto-rollback, incident response."""

import pytest

from ab_ops.reliability import (
    ErrorBudget,
    Incident,
    NothingToRollBackTo,
    ReleaseFrozen,
    ReleaseManager,
    Severity,
    handle_incident,
)


def test_error_budget_math() -> None:
    b = ErrorBudget(slo_target=0.99, window=1000)
    assert b.budget == 10
    assert b.exhausted(10) is False and b.exhausted(11) is True
    assert b.remaining(4) == 6


def test_deploy_then_rollback_reverts_to_previous() -> None:
    r = ReleaseManager(current="v1")
    r.deploy("v2")
    assert r.current == "v2" and r.previous == "v1"
    assert r.rollback() == "v1" and r.current == "v1"


def test_deploy_is_blocked_while_frozen() -> None:
    r = ReleaseManager(current="v1", frozen=True)
    with pytest.raises(ReleaseFrozen):
        r.deploy("v2")


def test_rollback_with_no_previous_raises() -> None:
    with pytest.raises(NothingToRollBackTo):
        ReleaseManager(current="v1").rollback()


def test_can_release_false_when_frozen_or_budget_exhausted() -> None:
    b = ErrorBudget(slo_target=0.99, window=1000)
    assert ReleaseManager("v1").can_release(b, errors=5) is True
    assert ReleaseManager("v1").can_release(b, errors=50) is False  # over budget
    assert ReleaseManager("v1", frozen=True).can_release(b, errors=0) is False


def test_sev1_with_pii_auto_rolls_back_freezes_and_flags_breach() -> None:
    r = ReleaseManager(current="v1")
    r.deploy("v2-bad")
    resp = handle_incident(Incident("i1", Severity.SEV1, touched_pii=True), r)
    assert resp.rolled_back and resp.rolled_back_to == "v1" and r.current == "v1"
    assert resp.release_frozen and r.frozen and not r.can_release()
    assert resp.postmortem_required and resp.breach_assessment_required


def test_sev3_without_pii_does_not_roll_back_or_freeze() -> None:
    r = ReleaseManager(current="v1")
    r.deploy("v2")
    resp = handle_incident(Incident("i2", Severity.SEV3, touched_pii=False), r)
    assert not resp.rolled_back and r.current == "v2"
    assert not resp.release_frozen and not resp.postmortem_required and not resp.breach_assessment_required


def test_budget_exhaustion_freezes_even_without_sev1() -> None:
    r = ReleaseManager(current="v1")
    b = ErrorBudget(slo_target=0.99, window=1000)
    resp = handle_incident(Incident("i3", Severity.SEV2, touched_pii=False), r, b, errors=500)
    assert resp.release_frozen and r.frozen  # error budget burned
    assert resp.postmortem_required and not resp.rolled_back  # Sev2 → postmortem, no rollback
