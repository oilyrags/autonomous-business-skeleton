"""Console 'Propose Experiment' form (PRD 0007 E2): an operator proposes an experiment, which is
dispatched through the governed GrowthPort. Infra-free (TestClient + stub port)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ab_console.auth import sign_identity

_OPERATOR = {
    "X-Operator-Id": "alice.ops",
    "X-Operator-Role": "operator",
    "X-Operator-Sig": sign_identity("alice.ops", "operator"),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    from ab_console.app import app

    with TestClient(app, headers=_OPERATOR) as c:
        yield c
    app.dependency_overrides.clear()


# --- build_proposal (pure) -----------------------------------------------------------------------


def test_build_proposal_makes_a_two_arm_experiment() -> None:
    from ab_console.viewmodels import build_proposal

    proposal = build_proposal(
        business_id="rocket",
        hypothesis="a shorter headline lifts signups",
        control_desc="current headline",
        treatment_desc="shorter headline",
        budget_minor=50_000,
        success_metrics=["activation_rate"],
    )
    assert proposal.business_id == "rocket"
    assert [a.name for a in proposal.arms] == ["control", "treatment"]
    assert proposal.arms[1].description == "shorter headline"
    assert proposal.budget_minor == 50_000


def test_build_proposal_rejects_an_empty_hypothesis() -> None:
    from ab_console.viewmodels import build_proposal

    with pytest.raises(ValueError):
        build_proposal(
            business_id="rocket",
            hypothesis="   ",
            control_desc="a",
            treatment_desc="b",
            budget_minor=50_000,
            success_metrics=["activation_rate"],
        )


# --- The governed propose route ------------------------------------------------------------------


def _form(**over: str) -> dict[str, str]:
    base = {
        "business_id": "rocket",
        "hypothesis": "a shorter headline lifts signups",
        "control_desc": "current headline",
        "treatment_desc": "shorter headline",
        "budget": "500",  # major units → 50_000 minor
        "success_metrics": "activation_rate, d7_revenue",
    }
    base.update(over)
    return base


def test_propose_routes_through_the_governed_port_with_the_real_operator(client: TestClient) -> None:
    from ab_console.app import app, growth_port_provider
    from ab_console.growth_port import StubGrowthPort

    stub = StubGrowthPort()
    app.dependency_overrides[growth_port_provider] = lambda: stub
    resp = client.post("/experiments/propose", data=_form())
    assert resp.status_code == 200
    assert len(stub.created) == 1
    proposal = stub.created[0]
    assert proposal["business_id"] == "rocket"
    assert proposal["budget_minor"] == 50_000  # 500 major → 50_000 minor
    assert proposal["maker"] == "alice.ops"  # the real, signature-verified operator (VULN-001)
    assert "exp_" in resp.text  # the created experiment id is shown


def test_propose_shows_a_friendly_error_on_bad_budget(client: TestClient) -> None:
    resp = client.post("/experiments/propose", data=_form(budget="not-a-number"))
    assert resp.status_code == 400
    assert "budget" in resp.text.lower()


def test_a_read_only_role_cannot_propose() -> None:
    from ab_console.app import app

    viewer = {
        "X-Operator-Id": "vic.viewer",
        "X-Operator-Role": "viewer",
        "X-Operator-Sig": sign_identity("vic.viewer", "viewer"),
    }
    with TestClient(app, headers=viewer) as c:
        assert c.post("/experiments/propose", data=_form()).status_code == 403
