"""Multi-agent GLM-5.2 ideation demo (PRD 0010 M4), deterministic + no infra.

    uv run python -m ab_growth.multiagent_demo   ·   make ideate-multiagent

Runs the whole pipeline on a CANNED agent (no GLM, no network): 3 generators → critic → synthesizer
→ the deterministic `ideation_gate`. Shows the advisory agent trace and the gated verdicts. With a
real model promoted for `ideation` (AB_IDEATION_PROVIDER=multiagent + AB_MODEL_PROVIDER=openrouter),
the same pipeline runs against live GLM-5.2 — the canned agent here just stands in for it.
"""

from __future__ import annotations

from ab_growth.ideate import (
    ExpectedImpact,
    IdeaCandidate,
    Scores,
    StubGroundingSource,
    ideate,
)
from ab_growth.multiagent import MultiAgentIdeationModel
from ab_schemas.models import Arm, ExperimentCreate

BUSINESS_ID = "acme-co"
PROMPT = "innovate a grounded growth bet to lift activation"


def _candidate(idea_id: str, title: str, novelty: int) -> IdeaCandidate:
    return IdeaCandidate(
        idea_id=idea_id,
        title=title,
        one_line_hook=f"{title} — grounded in the step-2 drop-off signal.",
        grounding_sources=["step-2 abandonment 38%"],
        scores=Scores(novelty=novelty, feasibility=4, market=4, grounding=4, experiment_clarity=4),
        expected_impact=ExpectedImpact(primary_metric="activation_rate", estimated_lift="+15%"),
        experiment=ExperimentCreate(
            business_id=BUSINESS_ID,
            hypothesis=f"{title} lifts activation",
            arms=[Arm(name="control", description="current"), Arm(name="treatment", description=title)],
            budget_minor=150_000,
            success_metrics=["activation_rate"],
        ),
    )


def _arr(*cands: IdeaCandidate) -> str:
    return "[" + ",".join(c.model_dump_json() for c in cands) + "]"


def _canned_agent(task_profile: str, prompt: str) -> str:
    """Stands in for GLM-5.2: one idea per generator lens, a critique, two synthesized winners."""
    p = prompt.lower()
    if "synthesizer" in p:
        return _arr(
            _candidate("syn-1", "Guided first-run checklist", novelty=4),
            _candidate("syn-2", "Async white-glove setup", novelty=3),
        )
    if "red-team critic" in p:
        return "gen-market and gen-adjacent overlap on onboarding; gen-contrarian is under-grounded."
    if "contrarian" in p:
        return _arr(_candidate("gen-contrarian", "Remove onboarding entirely", novelty=5))
    if "adjacent" in p:
        return _arr(_candidate("gen-adjacent", "Extend setup into the mobile app", novelty=3))
    return _arr(_candidate("gen-market", "Personalised first-run for the top segment", novelty=4))


def run(*, verbose: bool = True) -> int:
    echo = print if verbose else (lambda *_a, **_k: None)
    model = MultiAgentIdeationModel(agent_call=_canned_agent)
    result = ideate(BUSINESS_ID, PROMPT, model=model, grounding=StubGroundingSource(), count=2)

    echo(f"\n=== Multi-agent ideation — {BUSINESS_ID} ===")
    echo("  roster: 3 generators → critic → synthesizer (GLM-5.2 in a live deploy; canned here)")
    echo("  --- advisory agent trace ---")
    for lens, _out in model.last_trace.generators:
        echo(f"    generator[{lens}]: proposed")
    echo("    critic: challenged the pool")
    echo("    synthesizer: merged → final candidates")
    echo("  --- deterministic gate (authoritative) ---")
    for j in result.judged:
        echo(f"    [{j.verdict.value.upper():7}] {j.candidate.title} (score {j.overall}/5)")
    echo(f"  PROCEED → {len(result.proceed)} experiment-ready idea(s); the LLM proposed, the gate decided.")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
