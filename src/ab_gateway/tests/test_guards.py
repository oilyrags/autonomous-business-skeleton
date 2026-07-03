"""The two gateway-tool guards every governed handler repeats: `_validated` maps a bad args payload
to an audited ToolDenied(400) (never an uncaught 500), and `_require_serves` maps a cross-tenant
principal to ToolDenied(403). Infra-free."""

from __future__ import annotations

import pytest

from ab_gateway import authz
from ab_gateway.tools import ToolDenied, _require_serves, _validated
from ab_schemas.models import ExperimentCreate


def test_validated_returns_the_model_on_good_args() -> None:
    proposal = _validated(
        ExperimentCreate,
        {
            "business_id": "b",
            "hypothesis": "h",
            "arms": [{"name": "control"}, {"name": "treatment"}],
            "budget_minor": 1,
            "success_metrics": ["activation_rate"],
        },
        what="experiment",
    )
    assert isinstance(proposal, ExperimentCreate) and proposal.business_id == "b"


def test_validated_maps_bad_args_to_tool_denied_400() -> None:
    with pytest.raises(ToolDenied) as exc:
        _validated(ExperimentCreate, {"hypothesis": "no business_id"}, what="experiment")
    assert exc.value.status == 400 and "experiment" in exc.value.reason


def test_require_serves_denies_a_cross_tenant_principal(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(authz, "serves_business", lambda principal, business_id: False)
    with pytest.raises(ToolDenied) as exc:
        _require_serves("growth.experiment_design_agent", "acme")
    assert exc.value.status == 403 and "acme" in exc.value.reason


def test_require_serves_is_silent_when_authorized(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(authz, "serves_business", lambda principal, business_id: True)
    assert _require_serves("p", "acme") is None  # no raise = allowed
