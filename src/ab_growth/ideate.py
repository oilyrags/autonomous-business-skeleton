"""The ideation engine (PRD 0007 E4): a governed, skeleton-native multi-agent ideation pipeline.

Ground → generate → score → **deterministic gate** → design. The LLM (an injected `IdeationModel`
port over `model_gateway`) proposes ideas and *scores* them; a pure `ideation_gate` turns those
scores into a replayable PROCEED / REFINE / KILL verdict (ADR-0058 decision 8), so a non-deterministic
model never decides whether experiment budget is spent. Grounding comes from an injected
`GroundingSource` port (over `ab_data`/`ab_obs` reads). A PROCEED idea carries an embedded
`ExperimentCreate` payload, ready to go through the governed `growth.experiment.create` tool (E1/E5).

Every external seam is a port with a stub, so the whole ground→generate→score→gate pipeline is
deterministic in CI; real GLM-5.2 plugs in behind `IdeationModel` via Portkey (the `ab_evals` gate
applies), and real grounding behind `GroundingSource`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field

from ab_growth.proposer import ExperimentProposer, GrowthOutcome, StubExperimentProposer
from ab_schemas.models import Arm, ExperimentCreate

__all__ = ["ExperimentProposer", "GrowthOutcome", "StubExperimentProposer"]  # re-exported seam (#3)

# Gate thresholds (decision 8). An idea proceeds only if it clears the overall bar AND is novel
# enough AND is grounded enough; an idea with no cited grounding sources can never proceed.
GATE_OVERALL = 3.5
GATE_NOVELTY = 3
GATE_GROUNDING = 3
_REFINE_FLOOR = 2.5


class Verdict(StrEnum):
    PROCEED = "proceed"  # clears the bar → design + propose the experiment
    REFINE = "refine"  # promising but needs work (or grounding) before it spends budget
    KILL = "kill"  # not worth an experiment


class Scores(BaseModel):
    """The Validator's per-dimension rubric scores (1–5). Advisory — the gate is deterministic."""

    novelty: int = Field(ge=1, le=5)
    feasibility: int = Field(ge=1, le=5)
    market: int = Field(ge=1, le=5)
    grounding: int = Field(ge=1, le=5)
    experiment_clarity: int = Field(ge=1, le=5)


class ExpectedImpact(BaseModel):
    primary_metric: str
    estimated_lift: str = ""
    secondary_metrics: list[str] = Field(default_factory=list)
    business_case: str = ""


class IdeaCandidate(BaseModel):
    """A scored, grounded, experiment-ready concept (ideate.md §3, normalized to `business_id`)."""

    idea_id: str
    title: str
    one_line_hook: str = ""
    full_description: str = ""
    differentiation: str = ""
    mvp_notes: str = ""
    expected_impact: ExpectedImpact
    risks: list[str] = Field(default_factory=list)
    grounding_sources: list[str] = Field(default_factory=list)
    scores: Scores
    experiment: ExperimentCreate  # ready for growth.experiment.create


class GroundingReport(BaseModel):
    """The tenant-specific context pack the Analyst builds (ideate.md §9)."""

    grounding_summary: str = ""
    key_opportunity_signals: list[str] = Field(default_factory=list)
    white_space_areas: list[str] = Field(default_factory=list)
    relevant_prior_experiments: list[str] = Field(default_factory=list)
    recommended_focus_areas: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class JudgedIdea:
    candidate: IdeaCandidate
    overall: float
    verdict: Verdict


@dataclass(frozen=True)
class IdeationResult:
    business_id: str
    grounding: GroundingReport
    judged: list[JudgedIdea]

    @property
    def proceed(self) -> list[IdeaCandidate]:
        """The ideas that cleared the deterministic gate (their experiments are ready for E1)."""
        return [j.candidate for j in self.judged if j.verdict is Verdict.PROCEED]


# --- Ports (external seams; stubbed in CI, real adapters in a live deploy) --------------------------


class GroundingSource(Protocol):
    """Build the tenant-specific grounding context (over `ab_data`/`ab_obs`/prior experiments)."""

    def ground(self, business_id: str, prompt: str) -> GroundingReport: ...


class IdeationModel(Protocol):
    """The LLM: propose scored, experiment-ready candidates from the grounding context."""

    def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]: ...


# --- Pure scoring + gate (replayable; the LLM's scores are the only model-authored input) -----------


def overall_score(scores: Scores) -> float:
    """The class-leading score: the mean of the five rubric dimensions (0–5), to 2 dp. Pure."""
    dims = (scores.novelty, scores.feasibility, scores.market, scores.grounding, scores.experiment_clarity)
    return round(sum(dims) / len(dims), 2)


def ideation_gate(scores: Scores, grounding_sources: list[str]) -> Verdict:
    """Turn advisory rubric scores + grounding into a replayable verdict. An idea with no cited
    grounding sources can never PROCEED (anti-hallucination cap), but a weak idea is KILLed whether
    grounded or not — grounding gates PROCEED, not the REFINE/KILL floor."""
    overall = overall_score(scores)
    grounded = bool(grounding_sources)
    if (
        grounded
        and overall >= GATE_OVERALL
        and scores.novelty >= GATE_NOVELTY
        and scores.grounding >= GATE_GROUNDING
    ):
        return Verdict.PROCEED  # grounded and clears every bar
    if overall >= _REFINE_FLOOR:
        return Verdict.REFINE  # promising, or good-but-un-grounded → iterate / ground it first
    return Verdict.KILL  # weak — drop it, grounded or not


# --- Orchestration (pure over the injected ports) --------------------------------------------------


def judge_candidates(
    business_id: str, candidates: list[IdeaCandidate], *, grounding: GroundingReport
) -> IdeationResult:
    """Apply the deterministic gate to a set of already-generated candidates. Pure and replayable —
    the sole authority on PROCEED/REFINE/KILL. Reused to gate a partial (best-effort) candidate set
    when a run is aborted or times out (PRD 0011 A4)."""
    judged = [
        JudgedIdea(c, overall_score(c.scores), ideation_gate(c.scores, c.grounding_sources))
        for c in candidates
    ]
    return IdeationResult(business_id=business_id, grounding=grounding, judged=judged)


def ideate(
    business_id: str,
    prompt: str,
    *,
    model: IdeationModel,
    grounding: GroundingSource,
    count: int = 3,
) -> IdeationResult:
    """Run the pipeline: ground the tenant context, generate + score `count` candidates, then apply
    the deterministic gate to each. The PROCEED ideas carry experiments ready for E1/E5."""
    report = grounding.ground(business_id, prompt)
    candidates = model.propose(business_id, report, count)
    return judge_candidates(business_id, candidates, grounding=report)


def propose_ideas(result: IdeationResult, *, proposer: ExperimentProposer, maker: str) -> list[str]:
    """Dispatch every PROCEED idea's embedded experiment through the governed proposer (E5). Only
    gated-PROCEED ideas reach the create tool; the maker (the requesting operator/agent) is carried
    through for audit. Returns the created experiment ids (successful dispatches only)."""
    outcomes = [proposer.create(candidate.experiment, maker=maker) for candidate in result.proceed]
    return [o.experiment_id for o in outcomes if o.ok and o.experiment_id is not None]


# --- Stubs (deterministic CI) ----------------------------------------------------------------------


@dataclass
class StubGroundingSource:
    """A canned grounding report — no infra. A real adapter reads ab_data KPIs + prior experiments."""

    def ground(self, business_id: str, prompt: str) -> GroundingReport:
        return GroundingReport(
            grounding_summary=f"{business_id}: onboarding drop-off concentrated at step 2 ({prompt}).",
            key_opportunity_signals=["step-2 abandonment 38%", "activation below cohort median"],
            white_space_areas=["personalized first-run", "async setup"],
            relevant_prior_experiments=["exp-042: friction removal won (+18%)"],
            recommended_focus_areas=["reduce time-to-value"],
        )


class ModelGatewayIdeationModel:
    """The real LLM adapter: propose candidates via `model_gateway` (Portkey/GLM behind the eval
    gate). Degrades safely — when no eval-gated model is promoted, `model_gateway.complete` returns
    a fallback string, so we return no ideas rather than fabricate un-grounded ones."""

    def __init__(self, task_profile: str = "ideation") -> None:
        self._task_profile = task_profile

    def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
        import json

        from ab_gateway import model_gateway

        prompt = (
            f"Generate {count} grounded, experiment-ready product ideas for business '{business_id}'. "
            f"Grounding: {grounding.model_dump_json()}. Return a JSON array matching the IdeaCandidate "
            "schema (idea_id, title, expected_impact, grounding_sources, scores, experiment)."
        )
        raw = model_gateway.complete(self._task_profile, prompt)
        if raw.startswith("[fallback:"):  # no eval-gated model — abstain, do not fabricate
            return []
        try:
            payload = json.loads(raw)
            return [IdeaCandidate.model_validate(item) for item in payload][:count]
        except (json.JSONDecodeError, ValueError):
            return []  # malformed model output is dropped, never guessed


def _experiment(business_id: str, hypothesis: str, budget_minor: int) -> ExperimentCreate:
    return ExperimentCreate(
        business_id=business_id,
        hypothesis=hypothesis,
        arms=[Arm(name="control", description="current"), Arm(name="treatment", description="the change")],
        budget_minor=budget_minor,
        success_metrics=["activation_rate", "time_to_value"],
    )


@dataclass
class StubIdeationModel:
    """Three deterministic candidates spanning the gate outcomes: a strong grounded idea (PROCEED),
    a weak grounded idea (KILL), and a strong but un-grounded idea (capped to REFINE)."""

    def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
        impact = ExpectedImpact(primary_metric="activation_rate", estimated_lift="+25-40%")
        catalog = [
            IdeaCandidate(
                idea_id="idea-strong",
                title="Personalized first-run checklist",
                one_line_hook="Everyone gets to value on day one.",
                differentiation="Adapts to the account's declared goal, unlike a static tour.",
                expected_impact=impact,
                grounding_sources=["internal: ab_data step-2 drop-off cohort", "internal: exp-042 win"],
                scores=Scores(novelty=4, feasibility=5, market=5, grounding=5, experiment_clarity=4),
                experiment=_experiment(business_id, "a personalized first-run lifts activation", 80_000),
            ),
            IdeaCandidate(
                idea_id="idea-weak",
                title="Add a mascot animation",
                one_line_hook="A friendly robot waves hello.",
                expected_impact=impact,
                grounding_sources=["internal: brand survey"],
                scores=Scores(novelty=1, feasibility=2, market=1, grounding=2, experiment_clarity=2),
                experiment=_experiment(business_id, "a mascot lifts activation", 20_000),
            ),
            IdeaCandidate(
                idea_id="idea-ungrounded",
                title="Speculative AI copilot",
                one_line_hook="An assistant for everything.",
                expected_impact=impact,
                grounding_sources=[],  # no cited grounding → capped, cannot PROCEED
                scores=Scores(novelty=5, feasibility=3, market=4, grounding=1, experiment_clarity=3),
                experiment=_experiment(business_id, "a copilot lifts activation", 150_000),
            ),
        ]
        return catalog[:count]
