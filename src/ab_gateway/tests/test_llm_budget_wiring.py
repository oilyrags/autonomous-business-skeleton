"""complete_for_business end-to-end: the gateway meters LLM spend in the ledger and denies a
business-scoped model call once its budget would be breached. Runs against `make up-infra`."""

import uuid

import pytest

from ab_factory import store as factory_store
from ab_gateway.tools import ToolDenied, complete_for_business
from ab_growth.blueprint import Blueprint
from ab_ledger import store as ledger

AGENT = "executive.cmo_agent"
PROFILE = "executive_reasoning"


def _bp(business_id: str, *, llm_budget_minor: int) -> Blueprint:
    return Blueprint(
        business_id=business_id,
        name=business_id.title(),
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
        llm_budget_minor=llm_budget_minor,
    )


def test_call_within_budget_completes_and_meters_spend(clean_db: None) -> None:
    bid = f"acme{uuid.uuid4().hex[:6]}"
    factory_store.provision(_bp(bid, llm_budget_minor=50_000), capital_minor=500_000)

    out = complete_for_business(AGENT, bid, PROFILE, "hello", cost_minor=20_000)

    assert isinstance(out, str)
    assert ledger.account_balance(f"{bid}:llm_spend") == 20_000  # spend metered
    assert ledger.account_balance(f"{bid}:cash") == 500_000 - 20_000  # cash consumed
    assert ledger.trial_balance() == 0  # invariant holds


def test_call_that_would_breach_budget_is_denied_and_books_nothing(clean_db: None) -> None:
    bid = f"acme{uuid.uuid4().hex[:6]}"
    factory_store.provision(_bp(bid, llm_budget_minor=50_000), capital_minor=500_000)

    complete_for_business(AGENT, bid, PROFILE, "one", cost_minor=20_000)
    complete_for_business(AGENT, bid, PROFILE, "two", cost_minor=20_000)  # spend now 40_000

    with pytest.raises(ToolDenied) as exc:
        complete_for_business(AGENT, bid, PROFILE, "three", cost_minor=20_000)  # 60_000 > 50_000
    assert exc.value.status == 402
    assert ledger.account_balance(f"{bid}:llm_spend") == 40_000  # the denied call booked nothing


def test_unknown_business_is_denied(clean_db: None) -> None:
    with pytest.raises(ToolDenied) as exc:
        complete_for_business(AGENT, "nope", PROFILE, "hi", cost_minor=10_000)
    assert exc.value.status == 400
