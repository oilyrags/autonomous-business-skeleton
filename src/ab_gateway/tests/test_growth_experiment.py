"""growth.experiment.create (PRD 0007 E1): the governed experiment-proposal tool.

Infra-free tests exercise the arg model, the tenant/authority denials (which raise before any DB),
and the registry contract. The persist+emit happy path is infra-gated (mirrors test_business_payments)
and skips cleanly without `make up-infra`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ab_schemas.models import ExperimentCreate


def _proposal(business_id: str = "rocket", budget: int = 50_000) -> ExperimentCreate:
    return ExperimentCreate(
        business_id=business_id,
        hypothesis="a shorter headline lifts signups",
        arms=[{"name": "control"}, {"name": "treatment", "description": "shorter headline"}],
        budget_minor=budget,
        success_metrics=["activation_rate"],
    )


def test_experiment_proposal_requires_at_least_two_arms() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            business_id="rocket",
            hypothesis="a shorter headline lifts signups",
            arms=[{"name": "control"}],  # a single arm can't be an A/B test
            budget_minor=50_000,
            success_metrics=["activation_rate"],
        )


def test_create_denies_a_principal_that_does_not_serve_the_business() -> None:
    from ab_gateway import tools

    with pytest.raises(tools.ToolDenied) as exc:
        tools.create_experiment("mallory.agent", _proposal(business_id="rocket").model_dump())
    assert exc.value.status == 403  # cross-tenant proposal refused before the DB is touched


def test_create_rejects_invalid_args_as_a_400() -> None:
    from ab_gateway import tools

    with pytest.raises(tools.ToolDenied) as exc:
        tools.create_experiment("growth.experiment_design_agent", {"business_id": "rocket"})  # missing fields
    assert exc.value.status == 400


def test_the_tool_is_registered_with_a_governed_contract() -> None:
    from ab_gateway import tools

    spec = tools.get("growth.experiment.create")
    assert spec is not None
    assert spec.sensitive is True  # fails closed under an untrusted-input flow
    assert spec.side_effect == "write" and spec.egress is False


def test_the_design_agent_is_authorized_for_the_portfolio() -> None:
    from ab_gateway import authz

    assert authz.serves_business("growth.experiment_design_agent", "rocket") is True
    assert authz.serves_business("mallory.agent", "rocket") is False  # default-deny still holds


def test_created_event_carries_the_proposal_as_proposed() -> None:
    from ab_growth.experiment import to_created_event

    event = to_created_event(_proposal(), "exp-iq-1", producer="growth.experiment_design_agent")
    assert event.event_name == "ExperimentCreated"
    assert event.business_id == "rocket"
    assert event.experiment_id == "exp-iq-1"
    assert event.arm_names == ["control", "treatment"]
    assert event.budget_minor == 50_000
    assert event.status == "proposed"


# --- Persist + affordability (infra-gated: needs `make up-infra`) --------------------------------

DESIGN_AGENT = "growth.experiment_design_agent"


def _active_business(capital: int = 1_000_000) -> str:
    import uuid

    from ab_factory import store as factory
    from ab_growth.blueprint import Blueprint

    bid = f"biz{uuid.uuid4().hex[:8]}"
    factory.provision(  # funded, clean -> active
        Blueprint(
            business_id=bid,
            name=bid,
            target_revenue_minor=5_000_000,
            experiment_budget_minor=200_000,
            min_conversion_rate=0.04,
            max_cac_minor=5_000,
        ),
        capital_minor=capital,
    )
    return bid


def test_create_persists_a_proposal_without_moving_cash(clean_db: None) -> None:
    from ab_gateway import tools
    from ab_growth import store
    from ab_ledger import store as ledger

    bid = _active_business(capital=1_000_000)
    before = ledger.account_balance(f"{bid}:cash")
    exp_id = tools.create_experiment(DESIGN_AGENT, _proposal(business_id=bid, budget=50_000).model_dump())

    record = store.get(exp_id)
    assert record is not None
    assert record.business_id == bid and record.status == "proposed"
    assert record.arm_names == ["control", "treatment"] and record.budget_minor == 50_000
    assert ledger.account_balance(f"{bid}:cash") == before  # budget is a CAP — no cash moved
    assert [r.experiment_id for r in store.list_open(bid)] == [exp_id]  # tenant-scoped read


def test_create_is_denied_when_the_business_cannot_afford_the_budget(clean_db: None) -> None:
    from ab_gateway import tools

    bid = _active_business(capital=300_000)  # runway 300_000
    with pytest.raises(tools.ToolDenied) as exc:
        tools.create_experiment(DESIGN_AGENT, _proposal(business_id=bid, budget=500_000).model_dump())
    assert exc.value.status == 403 and "cannot afford" in exc.value.reason
