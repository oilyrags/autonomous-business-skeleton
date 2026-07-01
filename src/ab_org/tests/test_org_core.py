"""Hierarchical org: authority-based decision routing + escalation to human (pure, infra-free)."""

from __future__ import annotations

from ab_org.core import Charter, Org, route, team


def _org() -> Org:
    return Org(
        charters={
            "intern": Charter("intern", "Growth Intern", 1, "growth", reports_to="cmo"),
            "cmo": Charter("cmo", "CMO", 3, "growth", reports_to="ceo"),
            "ceo": Charter("ceo", "CEO", 4, "executive", reports_to=None),
        }
    )


def test_agent_decides_within_its_own_authority() -> None:
    r = route(_org(), initiator="intern", required_level=1)
    assert r.decider == "intern"
    assert r.path == ("intern",)
    assert r.escalated_to_human is False


def test_decision_escalates_up_to_a_sufficiently_senior_agent() -> None:
    r = route(_org(), initiator="intern", required_level=3)
    assert r.decider == "cmo"  # intern (L1) → cmo (L3)
    assert r.path == ("intern", "cmo")
    assert r.escalated_to_human is False


def test_l5_action_escalates_to_a_human_when_no_agent_holds_it() -> None:
    # No agent has L5 (money/high-risk is restricted) → it must reach a person.
    r = route(_org(), initiator="intern", required_level=5)
    assert r.decider is None
    assert r.path == ("intern", "cmo", "ceo")  # walked the whole chain
    assert r.escalated_to_human is True


def test_team_lists_a_department_most_senior_first() -> None:
    members = team(_org(), "growth")
    assert [c.agent_id for c in members] == ["cmo", "intern"]  # L3 before L1
