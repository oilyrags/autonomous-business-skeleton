"""Multi-agent GLM-5.2 ideation (PRD 0010 / ADR-0062).

Realizes "GLM-5.2 in multi-agentic mode to innovate new business ideas". A `MultiAgentIdeationModel`
adapter behind the existing `IdeationModel` port runs a fixed pipeline — **3 generators** (distinct
lenses) → **1 critic** (adversarial) → **1 synthesizer** — each GLM-5.2 on the governed `ideation`
profile. The agents are advisory; the pure `ideation_gate` still decides PROCEED/REFINE/KILL, and the
full reasoning is captured as an `AgentTrace` (shown distinctly, never fed to the gate).

Orchestration is pure over an injected ``agent_call(profile, prompt) -> str`` seam (default the governed
`model_gateway.complete`), so CI runs model-free with a canned agent. Degrades safely: an un-promoted
model makes each call abstain (``[fallback:…]``), so a run yields no ideas rather than fabrications.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from ab_growth.ideate import GroundingReport, IdeaCandidate

# (task_profile, prompt) -> raw model text. The one seam the whole pipeline is pure over.
AgentCall = Callable[[str, str], str]

# The three generator lenses (personas). One model + one profile; the persona is the only difference.
GENERATORS: tuple[tuple[str, str], ...] = (
    ("market_gap", "You are a market-gap scout: find an underserved segment or unmet need."),
    ("adjacent_expansion", "You are an adjacent-expansion strategist: extend the business's strengths."),
    ("contrarian", "You are a contrarian: take a counter-trend angle others would dismiss."),
)

_SCHEMA_HINT = (
    "Return ONLY a JSON array; each item matches the IdeaCandidate schema "
    "(idea_id, title, expected_impact{primary_metric}, grounding_sources, "
    "scores{novelty,feasibility,market,grounding,experiment_clarity 1-5}, "
    "experiment{business_id,hypothesis,arms,budget_minor,success_metrics})."
)


@dataclass
class AgentTrace:
    """The advisory reasoning from one multi-agent run. Shown distinctly in the console; NEVER an
    input to the deterministic gate."""

    generators: list[tuple[str, str]] = field(default_factory=list)  # (lens, raw output)
    critique: str = ""
    synthesis: str = ""


def _gateway_call(task_profile: str, prompt: str) -> str:
    from ab_gateway import model_gateway  # lazy: avoid an ab_growth -> ab_gateway import cycle

    return model_gateway.complete(task_profile, prompt)


def _parse_candidates(raw: str) -> list[IdeaCandidate]:
    """Parse a role's JSON output into candidates, degrading safely (abstain marker → none; malformed
    array or item → skipped, never guessed)."""
    if raw.startswith("[fallback:"):
        return []
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []
    out: list[IdeaCandidate] = []
    for item in payload if isinstance(payload, list) else []:
        try:
            out.append(IdeaCandidate.model_validate(item))
        except ValueError:
            continue
    return out


def _dedup(candidates: list[IdeaCandidate]) -> list[IdeaCandidate]:
    seen: set[str] = set()
    out: list[IdeaCandidate] = []
    for c in candidates:
        key = c.idea_id or c.title
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _generator_prompt(business_id: str, persona: str, grounding: GroundingReport, count: int) -> str:
    return (
        f"{persona} Innovate {count} grounded, experiment-ready business ideas for '{business_id}'. "
        f"Grounding: {grounding.model_dump_json()}. {_SCHEMA_HINT}"
    )


def _critic_prompt(candidates: list[IdeaCandidate], grounding: GroundingReport) -> str:
    titles = "; ".join(f"{c.idea_id}: {c.title}" for c in candidates)
    return (
        "You are a red-team critic. Adversarially critique these candidate ideas — flag weak "
        f"grounding, duplicates, and key risks. Candidates: [{titles}]. "
        f"Grounding: {grounding.model_dump_json()}. Return a concise critique (plain text)."
    )


def _synthesizer_prompt(
    business_id: str, candidates: list[IdeaCandidate], critique: str, grounding: GroundingReport, count: int
) -> str:
    pool = "; ".join(f"{c.idea_id}: {c.title}" for c in candidates)
    return (
        f"You are a synthesizer. Merge, de-duplicate, and sharpen the best of these ideas into the "
        f"top {count} for '{business_id}', addressing the critique. Candidates: [{pool}]. "
        f"Critique: {critique}. Grounding: {grounding.model_dump_json()}. {_SCHEMA_HINT}"
    )


class MultiAgentIdeationModel:
    """`IdeationModel` adapter: 3 generators → critic → synthesizer (5 calls/run). `last_trace` holds
    the most recent run's advisory reasoning for the console to surface."""

    def __init__(self, agent_call: AgentCall | None = None, *, task_profile: str = "ideation") -> None:
        self._call = agent_call or _gateway_call
        self._profile = task_profile
        self.last_trace: AgentTrace = AgentTrace()

    def propose(self, business_id: str, grounding: GroundingReport, count: int) -> list[IdeaCandidate]:
        generators: list[tuple[str, str]] = []
        pool: list[IdeaCandidate] = []
        for lens, persona in GENERATORS:
            raw = self._call(self._profile, _generator_prompt(business_id, persona, grounding, count))
            generators.append((lens, raw))
            pool.extend(_parse_candidates(raw))

        critique = self._call(self._profile, _critic_prompt(pool, grounding)) if pool else ""
        synthesis = (
            self._call(self._profile, _synthesizer_prompt(business_id, pool, critique, grounding, count))
            if pool
            else ""
        )
        self.last_trace = AgentTrace(generators=generators, critique=critique, synthesis=synthesis)

        final = _parse_candidates(synthesis)[:count]
        if not final:  # the synthesizer abstained/malformed — best-effort from the generators
            final = _dedup(pool)[:count]
        return final
