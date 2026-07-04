"""Async streaming ideation runner demo (PRD 0011 A5), deterministic + no infra.

    uv run python -m ab_growth.ideation_runner_demo   ·   make ideate-async

Drives the `InProcessIdeationRunner` end to end on a CANNED agent (no GLM, no bus): `start()` returns
a run_id immediately, then `stream()` yields started → per-agent progressed → complete, and the gated
cards come from the same deterministic gate. This is the non-blocking, streaming shape the `/growth`
console uses; with a model promoted for `ideation` the very same runner streams live GLM-5.2.
"""

from __future__ import annotations

import asyncio

from ab_growth.ideation_runner import Frame, InProcessIdeationRunner, RunStatus
from ab_growth.multiagent import MultiAgentIdeationModel

BUSINESS_ID = "acme-co"
PROMPT = "innovate a grounded growth bet to lift activation"

_CANDIDATE = (
    '{"idea_id":"%s","title":"%s","expected_impact":{"primary_metric":"activation_rate"},'
    '"grounding_sources":["step-2 abandonment 38%%"],'
    '"scores":{"novelty":%d,"feasibility":4,"market":4,"grounding":4,"experiment_clarity":4},'
    '"experiment":{"business_id":"acme-co","hypothesis":"%s lifts activation",'
    '"arms":[{"name":"control"},{"name":"treatment"}],"budget_minor":150000,'
    '"success_metrics":["activation_rate"]}}'
)


def _canned_agent(task_profile: str, prompt: str) -> str:
    """Stands in for GLM-5.2: one idea per generator lens, a critique, one synthesized winner."""
    p = prompt.lower()
    if "synthesizer" in p:
        return "[" + _CANDIDATE % ("syn-1", "Guided first-run checklist", 4, "guided first-run") + "]"
    if "red-team critic" in p:
        return "market-gap and adjacent overlap on onboarding; contrarian is under-grounded."
    lens = "market" if "market-gap" in p else "adjacent" if "adjacent" in p else "contrarian"
    novelty = 5 if lens == "contrarian" else 4
    return "[" + _CANDIDATE % (f"gen-{lens}", f"{lens} onboarding bet", novelty, lens) + "]"


def _print_frame(frame: Frame) -> None:
    kind = frame["type"]
    if kind == "started":
        print("  ● started (POST already returned — this streams in the background)")
    elif kind == "progressed":
        print(f"  ├─ {frame['step']} ✓")
    elif kind == "complete":
        print(f"  ● complete ({frame['candidate_count']} candidates)")
    elif kind == "failed":
        print(f"  ● failed ({frame['reason']})")


def run(*, verbose: bool = True) -> int:
    async def scenario() -> RunStatus:
        runner = InProcessIdeationRunner(
            model_factory=lambda: MultiAgentIdeationModel(agent_call=_canned_agent)
        )
        run_id = runner.start(BUSINESS_ID, PROMPT, operator="demo.operator")
        if verbose:
            print(f"POST /growth/ideate → run_id={run_id} (immediate)\n")
        async for frame in runner.stream(run_id):
            if verbose:
                _print_frame(frame)
        state = runner.snapshot(run_id)
        assert state is not None
        if verbose and state.result is not None:
            print("\nGated candidates (the deterministic gate decides, not the agents):")
            for j in state.result.judged:
                print(f"  [{j.verdict.value.upper():7}] {j.candidate.title}  score {j.overall}")
        return state.status

    status = asyncio.run(scenario())
    return 0 if status is RunStatus.COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(run())
