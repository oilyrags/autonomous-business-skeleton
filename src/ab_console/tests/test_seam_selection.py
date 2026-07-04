"""Phase-1 seam selection in the console (PRD 0009 S6): the kill-switch port and the ideation model
flip stub↔real by env; ideation stays usable (falls back to stub cards) when no model is promoted."""

from __future__ import annotations

from ab_console import app
from ab_console.killswitch_port import HttpKillSwitchPort, StubKillSwitchPort


def test_killswitch_port_defaults_to_stub(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_KILLSWITCH_PORT_PROVIDER", raising=False)
    assert isinstance(app.killswitch_port_provider(), StubKillSwitchPort)


def test_killswitch_port_http_when_selected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_KILLSWITCH_PORT_PROVIDER", "http")
    assert isinstance(app.killswitch_port_provider(), HttpKillSwitchPort)


def test_ideation_stays_usable_under_modelgateway_without_a_promoted_model(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # the real adapter abstains when its output isn't a usable spec; run_ideation must still render
    # cards (fall back to the deterministic stub) so the workspace is never empty
    monkeypatch.setenv("AB_IDEATION_PROVIDER", "modelgateway")
    result, _ = app.run_ideation("rocket", "lift activation")
    assert len(result.judged) > 0  # cards rendered via the safe fallback


def test_multiagent_ideation_selectable_and_stays_usable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # PRD 0010: AB_IDEATION_PROVIDER=multiagent runs the generators→critic→synthesizer adapter; with
    # no GLM promoted it abstains, so run_ideation falls back to the stub and still renders cards
    monkeypatch.setenv("AB_IDEATION_PROVIDER", "multiagent")
    result, _ = app.run_ideation("rocket", "lift activation")
    assert len(result.judged) > 0
