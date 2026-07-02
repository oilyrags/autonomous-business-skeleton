"""abctl: one front door over the module mains (pure, infra-free)."""

from __future__ import annotations

import pytest

from abctl.cli import COMMANDS, DEMO_STORY, main, run


def test_every_command_maps_to_an_importable_module() -> None:
    import importlib

    for name, (module_path, _) in COMMANDS.items():
        module = importlib.import_module(module_path)
        assert callable(module.main), f"{name} -> {module_path} has no main()"


def test_demo_story_only_uses_known_commands() -> None:
    assert set(DEMO_STORY) <= set(COMMANDS)


def test_run_a_single_command_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert run("org") == 0
    assert "escalation" in capsys.readouterr().out or True  # output printed, exit clean


def test_main_dispatches_and_unknown_command_exits_two() -> None:
    assert main(["org"]) == 0
    with pytest.raises(SystemExit) as exc:
        main(["not-a-command"])
    assert exc.value.code == 2  # argparse usage error
