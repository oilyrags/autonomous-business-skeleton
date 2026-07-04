"""Multi-agent ideation (PRD 0010 M1): 3 generators → critic → synthesizer behind the IdeationModel
port, pure over an injected agent-call seam (model-free CI). Infra-free."""

from __future__ import annotations

from ab_growth.ideate import ExpectedImpact, GroundingReport, IdeaCandidate, Scores
from ab_growth.multiagent import MultiAgentIdeationModel
from ab_schemas.models import Arm, ExperimentCreate

_GROUNDING = GroundingReport(grounding_summary="ctx", key_opportunity_signals=["sig"])


def _cand(idea_id: str) -> IdeaCandidate:
    return IdeaCandidate(
        idea_id=idea_id,
        title=f"idea {idea_id}",
        expected_impact=ExpectedImpact(primary_metric="activation_rate"),
        grounding_sources=["s1"],
        scores=Scores(novelty=4, feasibility=4, market=4, grounding=4, experiment_clarity=4),
        experiment=ExperimentCreate(
            business_id="b",
            hypothesis="h",
            arms=[Arm(name="control"), Arm(name="treatment")],
            budget_minor=1000,
            success_metrics=["activation_rate"],
        ),
    )


def _arr(*cands: IdeaCandidate) -> str:
    return "[" + ",".join(c.model_dump_json() for c in cands) + "]"


class _FakeAgent:
    """A canned agent: one candidate per generator, a critique, two synthesized candidates."""

    def __init__(self, *, synthesis: str | None = None) -> None:
        self.calls: list[str] = []
        self._synthesis = synthesis

    def __call__(self, profile: str, prompt: str) -> str:
        self.calls.append(prompt)
        p = prompt.lower()
        if "synthesizer" in p:
            if self._synthesis is not None:
                return self._synthesis
            return _arr(_cand("synth-1"), _cand("synth-2"))
        if "red-team critic" in p:
            return "risk: gen-1 and gen-2 overlap; ground gen-3 better."
        return _arr(_cand(f"gen-{len(self.calls)}"))  # a generator


def test_runs_the_full_roster_and_returns_the_synthesis() -> None:
    agent = _FakeAgent()
    model = MultiAgentIdeationModel(agent_call=agent)

    ideas = model.propose("b", _GROUNDING, count=2)

    assert len(agent.calls) == 5  # 3 generators + 1 critic + 1 synthesizer
    assert [i.idea_id for i in ideas] == ["synth-1", "synth-2"]  # the synthesizer's output is returned
    assert len(model.last_trace.generators) == 3 and model.last_trace.critique and model.last_trace.synthesis


def test_the_critic_sees_the_generator_candidates() -> None:
    agent = _FakeAgent()
    MultiAgentIdeationModel(agent_call=agent).propose("b", _GROUNDING, count=2)
    critic_prompt = next(c for c in agent.calls if "red-team critic" in c.lower())
    assert "gen-1" in critic_prompt  # generator candidates flow into the critic


def test_degrades_to_generator_ideas_when_the_synthesizer_abstains() -> None:
    agent = _FakeAgent(synthesis="[fallback:ideation] no eval-gated model — abstain")
    ideas = MultiAgentIdeationModel(agent_call=agent).propose("b", _GROUNDING, count=5)
    assert {i.idea_id for i in ideas} == {"gen-1", "gen-2", "gen-3"}  # best-effort from the generators


def test_all_abstain_yields_no_ideas_and_skips_downstream() -> None:
    def _abstain(profile: str, prompt: str) -> str:
        return "[fallback:ideation] no eval-gated model — abstain"

    agent_calls: list[str] = []

    def _counting(profile: str, prompt: str) -> str:
        agent_calls.append(prompt)
        return _abstain(profile, prompt)

    ideas = MultiAgentIdeationModel(agent_call=_counting).propose("b", _GROUNDING, count=3)
    assert ideas == []  # nothing fabricated
    assert len(agent_calls) == 3  # no candidates → critic + synthesizer are skipped
