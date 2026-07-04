"""Async, streaming ideation runner (PRD 0011 / ADR-0063).

Makes multi-agent ideation **non-blocking**. `start()` launches the existing `ideate()` pipeline in a
background `asyncio` task and returns a `run_id` immediately; `stream()` yields progress frames as the
run advances, ending on a terminal ``complete``/``failed`` frame; `snapshot()` returns the run's state
for a reload. State lives in an **ephemeral, capped in-process registry** (a restart drops in-flight
runs — acceptable for the stub; a detached-agent or persisted-job adapter behind the same
`IdeationRunner` port makes it durable later).

The pipeline itself is synchronous and does blocking model calls, so it runs in a **thread executor**
— the event loop stays free to serve the SSE stream. Per-agent progress (A2) is emitted from that
worker thread via a loop-affine, thread-safe hook. The deterministic `ideation_gate` is unchanged and
authoritative; frames are advisory transport, never an input to a decision.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from ab_growth.ideate import (
    GroundingSource,
    IdeationModel,
    IdeationResult,
    StubGroundingSource,
    ideate,
)
from ab_growth.multiagent import AgentTrace, StepHook
from ab_schemas.events import (
    Envelope,
    IdeationRunCompleted,
    IdeationRunFailed,
    IdeationRunStarted,
    build,
)

Frame = dict[str, object]  # a JSON-serializable SSE frame
EventSink = Callable[[Envelope], None]  # publishes a lifecycle event (bus/audit); injected, may block
_PRODUCER = "growth.ideation_runner"
_DEFAULT_MAX_RUNS = 32


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class RunState:
    """The advisory, ephemeral state of one ideation run (for streaming + reload). Not a decision."""

    run_id: str
    business_id: str
    prompt: str
    operator: str
    status: RunStatus = RunStatus.RUNNING
    result: IdeationResult | None = None
    trace: AgentTrace | None = None  # the advisory multi-agent reasoning (if the model exposes one)
    reason: str = ""  # populated on FAILED (timeout / killswitch / error)


@dataclass
class _Run:
    state: RunState
    queue: asyncio.Queue[Frame | None]  # a None sentinel marks end-of-stream


@runtime_checkable
class _SupportsProgress(Protocol):
    """A model that can report per-agent progress (e.g. the multi-agent adapter)."""

    on_step: StepHook | None


class IdeationRunner(Protocol):
    """The seam: kick off a run, stream its progress, read its state. The in-process runner is the
    stub; a detached-agent / persisted-job adapter implements the same interface later."""

    def start(self, business_id: str, prompt: str, *, operator: str) -> str: ...

    def stream(self, run_id: str) -> AsyncIterator[Frame]: ...

    def snapshot(self, run_id: str) -> RunState | None: ...


class InProcessIdeationRunner:
    """Runs ideation in an `asyncio` background task on the current event loop; one active run per
    business (a re-submit while one is in flight dedups to it, protecting the LLM budget)."""

    def __init__(
        self,
        *,
        model_factory: Callable[[], IdeationModel],
        grounding_factory: Callable[[], GroundingSource] = StubGroundingSource,
        count: int = 3,
        max_runs: int = _DEFAULT_MAX_RUNS,
        event_sink: EventSink | None = None,
    ) -> None:
        self._model_factory = model_factory
        self._grounding_factory = grounding_factory
        self._count = count
        self._max_runs = max_runs
        self._event_sink = event_sink
        self._runs: dict[str, _Run] = {}
        self._active: dict[str, str] = {}  # business_id -> the in-flight run_id
        self._seq = 0

    # -- public API -------------------------------------------------------------------------------

    def start(self, business_id: str, prompt: str, *, operator: str) -> str:
        active_id = self._active.get(business_id)
        if active_id is not None and self._runs[active_id].state.status is RunStatus.RUNNING:
            return active_id  # dedup: re-attach to the run already in flight
        self._seq += 1
        run_id = f"run_{business_id}_{self._seq}"
        run = _Run(RunState(run_id, business_id, prompt, operator), asyncio.Queue())
        self._runs[run_id] = run
        self._active[business_id] = run_id
        self._evict_oldest()
        asyncio.get_running_loop().create_task(self._run(run_id))
        return run_id

    async def stream(self, run_id: str) -> AsyncIterator[Frame]:
        run = self._runs.get(run_id)
        if run is None:
            return
        while True:
            frame = await run.queue.get()
            if frame is None:  # end-of-stream sentinel
                return
            yield frame

    def snapshot(self, run_id: str) -> RunState | None:
        run = self._runs.get(run_id)
        return run.state if run is not None else None

    # -- internals --------------------------------------------------------------------------------

    async def _run(self, run_id: str) -> None:
        run = self._runs[run_id]
        state = run.state
        loop = asyncio.get_running_loop()
        await run.queue.put({"type": "started", "run_id": run_id, "business_id": state.business_id})
        await self._publish(
            loop,
            build(
                IdeationRunStarted,
                subject=("business", state.business_id),
                producer=_PRODUCER,
                business_id=state.business_id,
                run_id=run_id,
                operator=state.operator,
                prompt=state.prompt,
            ),
        )

        def _emit_step(step: str, status: str) -> None:
            # called from the pipeline's worker/generator threads — marshal onto the event loop
            frame: Frame = {"type": "progressed", "step": step, "status": status}
            loop.call_soon_threadsafe(run.queue.put_nowait, frame)

        try:
            result, trace = await loop.run_in_executor(None, self._pipeline, state, _emit_step)
            state.result = result
            state.trace = trace
            state.status = RunStatus.COMPLETE
            await run.queue.put(
                {"type": "complete", "run_id": run_id, "candidate_count": len(result.judged)}
            )
            await self._publish(
                loop,
                build(
                    IdeationRunCompleted,
                    subject=("business", state.business_id),
                    producer=_PRODUCER,
                    business_id=state.business_id,
                    run_id=run_id,
                    candidate_count=len(result.judged),
                    proceed_count=len(result.proceed),
                ),
            )
        except Exception as exc:  # noqa: BLE001 - a detached run must surface, not swallow, failure
            state.status = RunStatus.FAILED
            state.reason = str(exc) or exc.__class__.__name__
            await run.queue.put({"type": "failed", "run_id": run_id, "reason": state.reason})
            await self._publish(
                loop,
                build(
                    IdeationRunFailed,
                    subject=("business", state.business_id),
                    producer=_PRODUCER,
                    business_id=state.business_id,
                    run_id=run_id,
                    reason=state.reason,
                ),
            )
        finally:
            if self._active.get(state.business_id) == run_id:
                self._active.pop(state.business_id, None)
            await run.queue.put(None)  # terminate any stream consumer

    async def _publish(self, loop: asyncio.AbstractEventLoop, event: Envelope) -> None:
        """Emit a lifecycle event through the injected sink, off the event loop (the sink may block on
        the bus). No sink (CI/dev without a bus) → a no-op; a sink failure never sinks the run."""
        if self._event_sink is None:
            return
        try:
            await loop.run_in_executor(None, self._event_sink, event)
        except Exception:  # noqa: BLE001 - the bus is best-effort; the run's result is authoritative
            pass

    def _pipeline(
        self, state: RunState, on_step: StepHook
    ) -> tuple[IdeationResult, AgentTrace | None]:
        """The blocking pipeline, run in a worker thread. Returns the result plus the model's advisory
        trace (if it exposes one). Attaches the progress hook to a progress-capable model (A2). The
        gate inside `ideate()` stays authoritative."""
        model = self._model_factory()
        if isinstance(model, _SupportsProgress):
            model.on_step = on_step
        result = ideate(
            state.business_id,
            state.prompt,
            model=model,
            grounding=self._grounding_factory(),
            count=self._count,
        )
        return result, getattr(model, "last_trace", None)

    def _evict_oldest(self) -> None:
        """Cap the registry — drop the oldest non-active runs (ephemeral, best-effort)."""
        while len(self._runs) > self._max_runs:
            for run_id in list(self._runs):
                if self._active.get(self._runs[run_id].state.business_id) != run_id:
                    del self._runs[run_id]
                    break
            else:
                break  # everything left is active — leave it
