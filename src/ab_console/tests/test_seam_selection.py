"""Phase-1 seam selection in the console (PRD 0009 S6): the kill-switch port and the ideation model
flip stub↔real by env; ideation stays usable (falls back to stub cards) when no model is promoted."""

from __future__ import annotations

import asyncio

from ab_console import app
from ab_console.killswitch_port import HttpKillSwitchPort, StubKillSwitchPort
from ab_growth.ideation_runner import InProcessIdeationRunner, RunStatus


def _run_ideation(business_id: str, prompt: str) -> object:
    """Drive the async runner to completion with the console's real model factory, returning the
    finished RunState — the seam that replaced the old sync run_ideation."""

    async def scenario() -> object:
        runner = InProcessIdeationRunner(model_factory=app._ideation_model)
        run_id = runner.start(business_id, prompt, operator="op.test")
        async for _frame in runner.stream(run_id):
            pass
        return runner.snapshot(run_id)

    return asyncio.run(scenario())


def test_killswitch_port_defaults_to_stub(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_KILLSWITCH_PORT_PROVIDER", raising=False)
    assert isinstance(app.killswitch_port_provider(), StubKillSwitchPort)


def test_killswitch_port_http_when_selected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_KILLSWITCH_PORT_PROVIDER", "http")
    assert isinstance(app.killswitch_port_provider(), HttpKillSwitchPort)


def test_ideation_stays_usable_under_modelgateway_without_a_promoted_model(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # the real adapter abstains when its output isn't a usable spec; the run must still render cards
    # (fall back to the deterministic stub) so the workspace is never empty
    monkeypatch.setenv("AB_IDEATION_PROVIDER", "modelgateway")
    state = _run_ideation("rocket", "lift activation")
    assert state.status is RunStatus.COMPLETE  # type: ignore[attr-defined]
    assert state.result is not None and len(state.result.judged) > 0  # type: ignore[attr-defined]


def test_multiagent_ideation_selectable_and_stays_usable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # PRD 0010: AB_IDEATION_PROVIDER=multiagent runs the generators→critic→synthesizer adapter; with
    # no GLM promoted it abstains, so the run falls back to the stub and still renders cards
    monkeypatch.setenv("AB_IDEATION_PROVIDER", "multiagent")
    state = _run_ideation("rocket", "lift activation")
    assert state.status is RunStatus.COMPLETE  # type: ignore[attr-defined]
    assert state.result is not None and len(state.result.judged) > 0  # type: ignore[attr-defined]
