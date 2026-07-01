"""Business Factory core (pure, infra-free): provision, readiness, activate, can_spend."""

from ab_factory.core import Status, provision
from ab_growth.blueprint import Blueprint

BP = Blueprint(
    business_id="acme",
    name="Acme",
    target_revenue_minor=1_000_000,
    experiment_budget_minor=200_000,
    min_conversion_rate=0.04,
    max_cac_minor=5_000,
)


def test_provision_funded_business_starts_draft() -> None:
    b = provision(BP, capital_minor=500_000)
    assert b.status is Status.DRAFT
    assert b.business_id == "acme"
    assert b.capital_minor == 500_000


def test_underfunded_provision_is_rejected() -> None:
    import pytest

    from ab_factory.core import Underfunded

    with pytest.raises(Underfunded):
        provision(BP, capital_minor=100_000)  # below experiment_budget 200_000


def test_readiness_ready_when_all_checks_pass() -> None:
    from ab_factory.core import readiness

    b = provision(BP, capital_minor=500_000)
    r = readiness(b, cash_balance=500_000, kill_switch_clear=True, compliance_clear=True)
    assert r.ready is True
    assert r.reasons == ()


def test_readiness_blocks_with_reasons_per_failing_check() -> None:
    from ab_factory.core import readiness

    b = provision(BP, capital_minor=500_000)
    underfunded = readiness(b, cash_balance=100_000, kill_switch_clear=True, compliance_clear=True)
    assert underfunded.ready is False and any("experiment budget" in r for r in underfunded.reasons)

    killed = readiness(b, cash_balance=500_000, kill_switch_clear=False, compliance_clear=True)
    assert killed.ready is False and any("kill switch" in r for r in killed.reasons)

    noncompliant = readiness(b, cash_balance=500_000, kill_switch_clear=True, compliance_clear=False)
    assert noncompliant.ready is False and any("compliance" in r for r in noncompliant.reasons)


def test_activate_only_when_ready() -> None:
    from ab_factory.core import Readiness, Status, activate

    b = provision(BP, capital_minor=500_000)
    activate(b, Readiness(ready=False, reasons=("kill switch active",)))
    assert b.status is Status.DRAFT  # blocked → stays draft (capital locked)

    activate(b, Readiness(ready=True, reasons=()))
    assert b.status is Status.ACTIVE  # cleared → active


def test_activate_after_a_blocker_clears() -> None:
    from ab_factory.core import Status, activate, readiness

    b = provision(BP, capital_minor=500_000)
    activate(b, readiness(b, cash_balance=500_000, kill_switch_clear=False, compliance_clear=True))
    assert b.status is Status.DRAFT
    activate(b, readiness(b, cash_balance=500_000, kill_switch_clear=True, compliance_clear=True))
    assert b.status is Status.ACTIVE


def test_can_spend_allows_active_within_runway() -> None:
    from ab_factory.core import Readiness, activate, can_spend

    b = provision(BP, capital_minor=500_000)
    activate(b, Readiness(ready=True, reasons=()))
    assert can_spend(b, 300_000, cash_balance=500_000).allowed is True


def test_can_spend_denies_when_not_active_nonpositive_or_over_runway() -> None:
    from ab_factory.core import Readiness, activate, can_spend

    draft = provision(BP, capital_minor=500_000)
    assert can_spend(draft, 100, cash_balance=500_000).allowed is False  # draft, not active

    b = provision(BP, capital_minor=500_000)
    activate(b, Readiness(ready=True, reasons=()))
    assert can_spend(b, 0, cash_balance=500_000).allowed is False  # non-positive
    over = can_spend(b, 600_000, cash_balance=500_000)  # exceeds remaining cash
    assert over.allowed is False and "insufficient" in over.reason.lower()


def test_business_activated_event_is_built_from_the_business() -> None:
    from ab_factory.core import Readiness, activate, to_event

    b = provision(BP, capital_minor=500_000)
    activate(b, Readiness(ready=True, reasons=()))
    ev = to_event(b)
    assert ev.event_name == "BusinessActivated"
    assert ev.business_id == "acme" and ev.name == "Acme" and ev.capital_minor == 500_000
