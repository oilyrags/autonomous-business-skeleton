"""Principal authorization facts: tenant binding + authority ceiling + no self-approval (pure)."""

from __future__ import annotations

import pytest

from ab_gateway import authz, tools


def test_unknown_principal_is_denied_everything() -> None:
    assert authz.serves_business("mallory.agent", "rocket") is False
    assert authz.authority_ceiling("mallory.agent") == 0
    assert authz.exceeds_authority("mallory.agent", 1) is True  # ceiling 0


def test_portfolio_principal_serves_any_business() -> None:
    # The skeleton's executive operator is granted the whole portfolio ("*").
    assert authz.serves_business("executive.cmo_agent", "rocket") is True
    assert authz.serves_business("executive.cmo_agent", "any-other") is True


def test_authority_ceiling_matches_the_registry() -> None:
    assert authz.authority_ceiling("executive.cmo_agent") == 3  # architecture/05_agent_registry.json
    assert authz.exceeds_authority("executive.cmo_agent", 3) is False
    assert authz.exceeds_authority("executive.cmo_agent", 4) is True  # can't claim above its level


def test_an_agent_cannot_self_assert_a_human_approval() -> None:
    assert authz.sanitize_approval_status("approved") == "autonomous_within_policy"  # downgraded
    assert authz.sanitize_approval_status("rejected") == "autonomous_within_policy"
    # what an agent MAY declare passes through untouched
    assert authz.sanitize_approval_status("autonomous_within_policy") == "autonomous_within_policy"
    assert authz.sanitize_approval_status("pending") == "pending"


# --- The gateway enforces the facts (denials raise before any DB/infra is touched) ----------------


def test_write_decision_denies_authority_above_ceiling() -> None:
    with pytest.raises(tools.ToolDenied) as exc:
        tools.write_decision("mallory.agent", {"decision_id": "d1", "title": "t", "authority_level": 5})
    assert exc.value.status == 403  # unknown principal, ceiling 0


def test_write_decision_denies_a_business_it_does_not_serve() -> None:
    with pytest.raises(tools.ToolDenied) as exc:
        tools.write_decision(
            "mallory.agent",
            {"decision_id": "d1", "title": "t", "authority_level": 0, "business_id": "rocket"},
        )
    assert exc.value.status == 403  # cross-tenant write refused


def test_business_spend_denies_a_principal_that_does_not_serve_the_business() -> None:
    with pytest.raises(tools.ToolDenied) as exc:
        tools._gate_business_spend("mallory.agent", "rocket", 100)
    assert exc.value.status == 403  # cross-tenant spend refused before the Factory/ledger is read
