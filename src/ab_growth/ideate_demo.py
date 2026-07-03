"""Ideation → governed experiment demo (PRD 0007 E5), deterministic + no infra.

    uv run python -m ab_growth.ideate_demo   ·   ./abctl ideate   ·   make ideate

Runs the governed ideation pipeline for one business: ground → generate → score → **deterministic
gate** → design, then dispatches each PROCEED idea's experiment through the governed proposer
(the same `growth.experiment.create` path a live deploy uses). The stub LLM stands in for GLM-5.2;
the gate, scoring, and dispatch are the real, replayable code.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_growth.ideate import (
    StubExperimentProposer,
    StubGroundingSource,
    StubIdeationModel,
    Verdict,
    ideate,
    propose_ideas,
)

BID = "inboxiq"
PROMPT = "reduce onboarding drop-off at step 2"
MAKER = "growth.experiment_design_agent"

_BADGE = {Verdict.PROCEED: "PROCEED", Verdict.REFINE: "REFINE", Verdict.KILL: "KILL  "}


@dataclass(frozen=True)
class IdeateDemoSummary:
    candidates: int
    proceeded: int
    experiments_created: int


def run(*, verbose: bool = True) -> IdeateDemoSummary:
    echo = print if verbose else (lambda *_a, **_k: None)

    result = ideate(BID, PROMPT, model=StubIdeationModel(), grounding=StubGroundingSource(), count=3)

    echo(f"\n=== Ideate for {BID!r} — {PROMPT} ===")
    echo(f"  grounding: {result.grounding.grounding_summary}")
    echo("\n  candidates (LLM scores are advisory; the verdict is the deterministic gate):")
    for j in result.judged:
        grounded = "grounded" if j.candidate.grounding_sources else "UN-GROUNDED"
        echo(f"    [{_BADGE[j.verdict]}] {j.candidate.title:34} score {j.overall:.1f}  ({grounded})")

    proposer = StubExperimentProposer()
    ids = propose_ideas(result, proposer=proposer, maker=MAKER)

    echo("\n  governed experiments created (only PROCEED ideas reach growth.experiment.create):")
    for created, exp_id in zip(proposer.created, ids, strict=True):
        echo(f"    {exp_id}  ·  {created['business_id']}  ·  maker={created['maker']}")
        echo(f'      "{created["hypothesis"]}"')

    echo(
        f"\n  {len(result.judged)} candidates → {len(result.proceed)} proceeded → "
        f"{len(ids)} governed experiment(s). No LLM decided money; the gate + create are deterministic."
    )
    return IdeateDemoSummary(
        candidates=len(result.judged),
        proceeded=len(result.proceed),
        experiments_created=len(ids),
    )


def main() -> int:
    summary = run()
    ok = summary.experiments_created == summary.proceeded and summary.proceeded >= 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
