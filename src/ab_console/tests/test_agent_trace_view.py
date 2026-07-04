"""The advisory agent trace surfaces in the growth workspace view (PRD 0010 M3), distinct from the
deterministic verdict. Pure/infra-free."""

from __future__ import annotations

from ab_console.viewmodels import ideation_workspace
from ab_growth.ideate import GroundingReport, IdeationResult
from ab_growth.multiagent import AgentTrace


def _empty_result() -> IdeationResult:
    return IdeationResult(business_id="rocket", grounding=GroundingReport(grounding_summary="ctx"), judged=[])


def test_workspace_flattens_the_agent_trace_in_order() -> None:
    trace = AgentTrace(
        generators=[("market_gap", "g1"), ("adjacent_expansion", "g2"), ("contrarian", "g3")],
        critique="c",
        synthesis="s",
    )
    view = ideation_workspace(_empty_result(), trace=trace)
    roles = [role for role, _ in view.agent_trace]
    assert roles == ["market_gap", "adjacent_expansion", "contrarian", "critic", "synthesizer"]


def test_no_trace_means_no_agent_trace_rows() -> None:
    assert ideation_workspace(_empty_result()).agent_trace == []
