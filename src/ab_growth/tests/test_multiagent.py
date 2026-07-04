"""Multi-agent ideation (PRD 0010 M1): 3 generators → critic → synthesizer behind the IdeationModel
port, pure over an injected agent-call seam (model-free CI). Infra-free."""

from __future__ import annotations

import threading

from ab_growth.ideate import ExpectedImpact, GroundingReport, IdeaCandidate, Scores
from ab_growth.multiagent import GENERATORS, MultiAgentIdeationModel
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
    """A canned agent: one candidate per generator, a critique, two synthesized candidates. Thread-safe
    and order-independent — generators run concurrently, so the candidate id is derived from the
    persona in the prompt, not the call count."""

    def __init__(self, *, synthesis: str | None = None) -> None:
        self.calls: list[str] = []
        self._synthesis = synthesis
        self._lock = threading.Lock()

    def __call__(self, profile: str, prompt: str) -> str:
        with self._lock:
            self.calls.append(prompt)
        p = prompt.lower()
        if "synthesizer" in p:
            if self._synthesis is not None:
                return self._synthesis
            return _arr(_cand("synth-1"), _cand("synth-2"))
        if "red-team critic" in p:
            return "risk: gen-1 and gen-2 overlap; ground gen-3 better."
        for i, (_lens, persona) in enumerate(GENERATORS, start=1):
            if persona.lower() in p:  # a generator — stable id per persona
                return _arr(_cand(f"gen-{i}"))
        raise AssertionError(f"unexpected agent prompt: {prompt!r}")


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


def test_multiagent_demo_runs_to_proceed_candidates() -> None:
    from ab_growth.multiagent_demo import run

    assert run(verbose=False) == 0  # the canned pipeline reaches gated PROCEED candidates


def test_parser_coerces_string_arms_and_json_fences() -> None:
    from ab_growth.multiagent import _parse_candidates

    # a real model often emits arms as descriptive strings and wraps the array in ```json fences
    body = _cand("real-1").model_dump_json()
    import json as _json

    obj = _json.loads(body)
    obj["experiment"]["arms"] = ["Control: current step-2", "Treatment: pre-filled step-2"]
    raw = "```json\n[" + _json.dumps(obj) + "]\n```"

    cands = _parse_candidates(raw)
    assert len(cands) == 1
    assert cands[0].experiment.arms[0].name == "control"  # string arm coerced to an Arm
    assert cands[0].experiment.arms[1].name == "treatment"
