"""Async streaming ideation runner (PRD 0011 A1): start() returns a run_id immediately, stream()
yields progress frames ending on a terminal complete/failed frame, and a re-submit while a run is in
flight dedups to it. Driven with asyncio.run (no pytest-asyncio in the repo). Infra-free."""

from __future__ import annotations

import asyncio

from ab_growth.ideate import (
    ExpectedImpact,
    GroundingReport,
    IdeaCandidate,
    Scores,
    StubGroundingSource,
    StubIdeationModel,
)
from ab_growth.ideation_runner import InProcessIdeationRunner, RunStatus
from ab_schemas.models import Arm, ExperimentCreate


async def _drain(runner: InProcessIdeationRunner, run_id: str) -> list[dict[str, object]]:
    return [frame async for frame in runner.stream(run_id)]


def test_start_returns_a_run_id_and_streams_started_then_complete() -> None:
    async def scenario() -> tuple[str, list[dict[str, object]], RunStatus]:
        runner = InProcessIdeationRunner(model_factory=StubIdeationModel)
        run_id = runner.start("acme", "lift activation", operator="op.alice")
        frames = await _drain(runner, run_id)
        snap = runner.snapshot(run_id)
        assert snap is not None
        return run_id, frames, snap.status

    run_id, frames, status = asyncio.run(scenario())

    assert run_id.startswith("run_")
    types = [f["type"] for f in frames]
    assert types[0] == "started"  # submit is acknowledged immediately
    assert types[-1] == "complete"  # the stream reaches a terminal frame
    assert status is RunStatus.COMPLETE
    # the terminal frame reports the gated candidate count (StubIdeationModel judges 3)
    assert frames[-1]["candidate_count"] == 3


def test_resubmit_while_running_dedups_to_the_same_run() -> None:
    async def scenario() -> tuple[str, str]:
        runner = InProcessIdeationRunner(model_factory=StubIdeationModel)
        # two synchronous starts before any await → the first task hasn't run yet (still RUNNING)
        first = runner.start("acme", "p", operator="op")
        second = runner.start("acme", "p", operator="op")
        await _drain(runner, first)
        return first, second

    first, second = asyncio.run(scenario())
    assert first == second  # budget-safe: no second GLM run for the same in-flight business


def test_a_new_run_starts_once_the_previous_one_finishes() -> None:
    async def scenario() -> tuple[str, str]:
        runner = InProcessIdeationRunner(model_factory=StubIdeationModel)
        first = runner.start("acme", "p", operator="op")
        await _drain(runner, first)  # let it complete → active slot frees
        second = runner.start("acme", "p", operator="op")
        await _drain(runner, second)
        return first, second

    first, second = asyncio.run(scenario())
    assert first != second


def test_a_failing_pipeline_terminates_the_stream_with_a_failed_frame() -> None:
    class _Boom:
        def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
            raise RuntimeError("model exploded")

    async def scenario() -> tuple[list[dict[str, object]], RunStatus]:
        runner = InProcessIdeationRunner(model_factory=_Boom)
        run_id = runner.start("acme", "p", operator="op")
        frames = await _drain(runner, run_id)
        snap = runner.snapshot(run_id)
        assert snap is not None
        return frames, snap.status

    frames, status = asyncio.run(scenario())
    assert frames[-1]["type"] == "failed"  # never hangs — always reaches a terminal frame
    assert status is RunStatus.FAILED


def test_snapshot_is_none_for_an_unknown_run() -> None:
    runner = InProcessIdeationRunner(model_factory=StubIdeationModel)
    assert runner.snapshot("run_nope") is None


def test_grounding_factory_is_injectable() -> None:
    # a candidate-free model still completes cleanly (0 candidates, not a crash)
    class _Empty:
        def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
            return []

    async def scenario() -> list[dict[str, object]]:
        runner = InProcessIdeationRunner(model_factory=_Empty, grounding_factory=StubGroundingSource)
        run_id = runner.start("acme", "p", operator="op")
        return await _drain(runner, run_id)

    frames = asyncio.run(scenario())
    assert frames[-1]["type"] == "complete"
    assert frames[-1]["candidate_count"] == 0


# a canned candidate for any future fixture needs (keeps imports honest)
_SAMPLE = IdeaCandidate(
    idea_id="x",
    title="t",
    expected_impact=ExpectedImpact(primary_metric="activation_rate"),
    grounding_sources=["s"],
    scores=Scores(novelty=4, feasibility=4, market=4, grounding=4, experiment_clarity=4),
    experiment=ExperimentCreate(
        business_id="acme",
        hypothesis="h",
        arms=[Arm(name="control"), Arm(name="treatment")],
        budget_minor=1000,
        success_metrics=["activation_rate"],
    ),
)
