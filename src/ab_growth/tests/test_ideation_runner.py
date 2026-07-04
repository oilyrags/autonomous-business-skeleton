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


def test_progress_frames_stream_between_started_and_complete() -> None:
    # PRD 0011 A2: a progress-capable model (the multi-agent adapter) streams a `progressed` frame per
    # agent, framed by started…complete. Uses a canned agent_call so it's model-free.
    from ab_growth.multiagent import MultiAgentIdeationModel

    def _canned(profile: str, prompt: str) -> str:
        p = prompt.lower()
        if "synthesizer" in p:
            return _arr(_SAMPLE)
        if "red-team critic" in p:
            return "ok"
        return _arr(_SAMPLE)  # each generator

    async def scenario() -> list[dict[str, object]]:
        runner = InProcessIdeationRunner(model_factory=lambda: MultiAgentIdeationModel(agent_call=_canned))
        run_id = runner.start("acme", "p", operator="op")
        return await _drain(runner, run_id)

    frames = asyncio.run(scenario())
    types = [f["type"] for f in frames]
    assert types[0] == "started" and types[-1] == "complete"
    steps = {f["step"] for f in frames if f["type"] == "progressed"}
    assert steps == {"market_gap", "adjacent_expansion", "contrarian", "critic", "synthesizer"}


def _arr(cand: IdeaCandidate) -> str:
    return "[" + cand.model_dump_json() + "]"


def test_lifecycle_events_are_emitted_to_the_sink() -> None:
    # PRD 0011 A3: the runner emits IdeationRunStarted then a terminal IdeationRunCompleted to the
    # injected sink (bus/audit). The candidate/proceed counts come from the deterministic gate.
    events: list[object] = []

    async def scenario() -> str:
        runner = InProcessIdeationRunner(model_factory=StubIdeationModel, event_sink=events.append)
        run_id = runner.start("acme", "lift activation", operator="op.alice")
        await _drain(runner, run_id)
        return run_id

    run_id = asyncio.run(scenario())
    names = [type(e).__name__ for e in events]
    assert names == ["IdeationRunStarted", "IdeationRunCompleted"]
    started, completed = events
    assert started.business_id == "acme" and started.run_id == run_id  # type: ignore[attr-defined]
    assert started.operator == "op.alice"  # type: ignore[attr-defined]
    assert completed.candidate_count == 3 and completed.proceed_count == 1  # type: ignore[attr-defined]


def test_a_failed_run_emits_ideationrunfailed() -> None:
    events: list[object] = []

    class _Boom:
        def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
            raise RuntimeError("model exploded")

    async def scenario() -> None:
        runner = InProcessIdeationRunner(model_factory=_Boom, event_sink=events.append)
        run_id = runner.start("acme", "p", operator="op")
        await _drain(runner, run_id)

    asyncio.run(scenario())
    assert [type(e).__name__ for e in events] == ["IdeationRunStarted", "IdeationRunFailed"]
    assert events[-1].reason  # type: ignore[attr-defined]


def test_no_sink_means_no_publish_and_no_crash() -> None:
    # dev/CI without a bus: the runner takes no sink and still completes cleanly
    async def scenario() -> str:
        runner = InProcessIdeationRunner(model_factory=StubIdeationModel)  # no event_sink
        run_id = runner.start("acme", "p", operator="op")
        frames = await _drain(runner, run_id)
        return frames[-1]["type"]  # type: ignore[return-value]

    assert asyncio.run(scenario()) == "complete"


def test_a_halted_business_fails_without_spending() -> None:
    # PRD 0011 A4: a halted kill switch fails the run before the model is ever invoked (no GLM spend)
    calls: list[int] = []

    class _Tracked:
        def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
            calls.append(1)
            return []

    async def scenario() -> tuple[list[dict[str, object]], RunStatus]:
        runner = InProcessIdeationRunner(model_factory=_Tracked, is_halted=lambda: True)
        run_id = runner.start("acme", "p", operator="op")
        frames = await _drain(runner, run_id)
        snap = runner.snapshot(run_id)
        assert snap is not None
        return frames, snap.status

    frames, status = asyncio.run(scenario())
    assert frames[-1]["type"] == "failed" and frames[-1]["reason"] == "killswitch"
    assert status is RunStatus.FAILED
    assert calls == []  # the model was never called — nothing spent


def test_a_slow_run_times_out_with_a_failed_frame() -> None:
    import time

    class _Slow:
        def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
            time.sleep(0.5)
            return []

    async def scenario() -> tuple[list[dict[str, object]], RunStatus]:
        runner = InProcessIdeationRunner(model_factory=_Slow, timeout_s=0.05)
        run_id = runner.start("acme", "p", operator="op")
        frames = await _drain(runner, run_id)
        snap = runner.snapshot(run_id)
        assert snap is not None
        return frames, snap.status

    frames, status = asyncio.run(scenario())
    assert frames[-1]["type"] == "failed" and frames[-1]["reason"] == "timeout"
    assert status is RunStatus.FAILED


def test_a_midrun_abort_stops_spend_and_surfaces_partials() -> None:
    # a kill switch that trips during the generators aborts before the critic/synthesizer calls, and
    # the generator pool is still gated into best-effort partial cards
    from ab_growth.multiagent import MultiAgentIdeationModel

    calls: list[str] = []
    tripped = {"v": False}

    def _canned(profile: str, prompt: str) -> str:
        calls.append(prompt.lower())
        tripped["v"] = True  # once a generator has run, arm the kill switch
        return _arr(_SAMPLE)

    async def scenario() -> tuple[list[dict[str, object]], object]:
        runner = InProcessIdeationRunner(
            model_factory=lambda: MultiAgentIdeationModel(agent_call=_canned),
            is_halted=lambda: tripped["v"],
        )
        run_id = runner.start("acme", "p", operator="op")
        frames = await _drain(runner, run_id)
        return frames, runner.snapshot(run_id)

    frames, snap = asyncio.run(scenario())
    assert frames[-1]["type"] == "failed" and frames[-1]["reason"] == "killswitch"
    assert not any("critic" in c or "synthesizer" in c for c in calls)  # spend stopped before them
    assert snap.result is not None and len(snap.result.judged) >= 1  # type: ignore[attr-defined]


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
