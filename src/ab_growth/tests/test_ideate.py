"""The ideation engine (PRD 0007 E4): ground → generate → score → deterministic gate → design.

Fully infra-free: the LLM and grounding are injected ports, stubbed here. The gate is a pure
function (LLM scores are advisory; the PROCEED/REFINE/KILL threshold is replayable — ADR-0058
decision 8)."""

from __future__ import annotations

from ab_growth.ideate import (
    GroundingReport,
    ModelGatewayIdeationModel,
    Scores,
    StubExperimentProposer,
    StubGroundingSource,
    StubIdeationModel,
    Verdict,
    ideate,
    ideation_gate,
    overall_score,
    propose_ideas,
)


def test_ideate_proceeds_a_strong_grounded_idea_ready_for_the_create_tool() -> None:
    result = ideate(
        "rocket",
        "reduce onboarding drop-off",
        model=StubIdeationModel(),
        grounding=StubGroundingSource(),
        count=3,
    )
    assert Verdict.PROCEED in [j.verdict for j in result.judged]
    top = result.proceed[0]
    assert top.experiment.business_id == "rocket"  # the embedded proposal is ready for E1
    assert len(top.experiment.arms) >= 2
    assert len(top.grounding_sources) > 0  # a PROCEED idea is grounded


def test_overall_score_is_the_mean_of_the_rubric() -> None:
    scores = Scores(novelty=4, feasibility=5, market=5, grounding=5, experiment_clarity=4)
    assert overall_score(scores) == 4.6  # (4+5+5+5+4)/5


def test_gate_proceeds_a_strong_grounded_idea() -> None:
    strong = Scores(novelty=4, feasibility=5, market=5, grounding=5, experiment_clarity=4)
    assert ideation_gate(strong, ["internal: cohort analysis"]) is Verdict.PROCEED


def test_gate_caps_an_ungrounded_idea_even_with_top_scores() -> None:
    top = Scores(novelty=5, feasibility=5, market=5, grounding=5, experiment_clarity=5)
    assert ideation_gate(top, []) is Verdict.REFINE  # no cited grounding → never PROCEED


def test_gate_kills_a_weak_idea() -> None:
    weak = Scores(novelty=1, feasibility=2, market=1, grounding=2, experiment_clarity=2)
    assert ideation_gate(weak, ["internal: brand survey"]) is Verdict.KILL


def test_only_grounded_high_scorers_proceed_through_the_pipeline() -> None:
    result = ideate("rocket", "x", model=StubIdeationModel(), grounding=StubGroundingSource(), count=3)
    assert {c.idea_id for c in result.proceed} == {"idea-strong"}
    by_id = {j.candidate.idea_id: j.verdict for j in result.judged}
    assert by_id["idea-weak"] is Verdict.KILL
    assert by_id["idea-ungrounded"] is Verdict.REFINE  # strong scores, but un-grounded


# --- E5: wire ideation → governed create ---------------------------------------------------------


def test_propose_ideas_dispatches_only_the_proceed_ideas() -> None:
    result = ideate("rocket", "reduce drop-off", model=StubIdeationModel(), grounding=StubGroundingSource())
    proposer = StubExperimentProposer()
    ids = propose_ideas(result, proposer=proposer, maker="ops.alice")
    assert len(ids) == 1  # only idea-strong proceeded → exactly one governed experiment
    assert proposer.created[0]["business_id"] == "rocket"
    assert proposer.created[0]["maker"] == "ops.alice"  # attribution flows to the governed create


def test_real_model_abstains_without_a_promoted_model() -> None:
    # model_gateway returns a fallback string when no eval-gated model is promoted (the default),
    # so the real adapter degrades safely to no ideas rather than fabricating.
    out = ModelGatewayIdeationModel().propose("rocket", GroundingReport(), 3)
    assert out == []


def test_ideate_demo_creates_exactly_the_proceed_experiments() -> None:
    from ab_growth.ideate_demo import run

    summary = run(verbose=False)
    assert summary.candidates == 3
    assert summary.proceeded == 1  # one strong grounded idea cleared the gate
    assert summary.experiments_created == summary.proceeded  # each PROCEED → one governed experiment


def test_ideate_demo_cli_exits_zero() -> None:
    from ab_growth.ideate_demo import main

    assert main() == 0
