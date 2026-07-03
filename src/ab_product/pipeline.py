"""The gated SDLC state machine (PRD 0008 P2): the stages a promoted initiative travels and the
gates that admit each. Pure and deterministic — a failed gate halts the initiative (the
instantiation-guide model); the DPIA and launch gates are human, so the machine pauses at them and
only a recorded human approval moves past. Persistence + events live in `ab_product.store`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Stage(StrEnum):
    INTAKE = "intake"
    SPEC = "spec"
    DESIGN = "design"
    DPIA = "dpia"  # human gate (DPO sign-off when personal data is processed)
    BLUEPRINT = "blueprint"
    SCAFFOLD = "scaffold"
    QA = "qa"
    LAUNCH = "launch"  # human gate (CEO/CISO launch approval)
    LAUNCHED = "launched"  # terminal


_ORDER: tuple[Stage, ...] = (
    Stage.INTAKE,
    Stage.SPEC,
    Stage.DESIGN,
    Stage.DPIA,
    Stage.BLUEPRINT,
    Stage.SCAFFOLD,
    Stage.QA,
    Stage.LAUNCH,
    Stage.LAUNCHED,
)
HUMAN_STAGES = frozenset({Stage.DPIA, Stage.LAUNCH})
_TERMINAL = Stage.LAUNCHED


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str = ""


@dataclass(frozen=True)
class PipelineState:
    initiative_id: str
    business_id: str
    stage: Stage
    status: str  # in_progress | awaiting_human | halted | launched
    reason: str = ""


def _next(stage: Stage) -> Stage:
    return _ORDER[_ORDER.index(stage) + 1]


def _status_for(stage: Stage) -> str:
    if stage is _TERMINAL:
        return "launched"
    if stage in HUMAN_STAGES:
        return "awaiting_human"
    return "in_progress"


def start(initiative_id: str, business_id: str) -> PipelineState:
    return PipelineState(initiative_id, business_id, Stage.INTAKE, "in_progress")


def advance(state: PipelineState, gate: GateResult) -> PipelineState:
    """Apply a deterministic stage gate: pass → the next stage; fail → halt here. Only valid on an
    in-progress, non-human, non-terminal stage (a human stage needs `approve_human`)."""
    if state.status != "in_progress" or state.stage in HUMAN_STAGES or state.stage is _TERMINAL:
        raise ValueError(f"cannot advance from {state.stage}/{state.status}")
    if not gate.ok:
        return PipelineState(state.initiative_id, state.business_id, state.stage, "halted", gate.reason)
    nxt = _next(state.stage)
    return PipelineState(state.initiative_id, state.business_id, nxt, _status_for(nxt))


def approve_human(state: PipelineState, *, actor: str) -> PipelineState:
    """Record a plain human approval at a human gate (e.g. launch) and move to the next stage.

    The DPIA gate is deliberately NOT resolvable here: it must run the personal-data assessment, so
    it can only be cleared via `ab_product.compliance.clear_dpia` — otherwise a personal-data
    initiative could be waved through the gate without a DPIA. Any other human gate approves here."""
    if state.stage is Stage.DPIA:
        raise ValueError("the DPIA gate must be resolved via ab_product.compliance.clear_dpia")
    if state.status != "awaiting_human":
        raise ValueError(f"no human approval pending at {state.stage}/{state.status}")
    nxt = _next(state.stage)
    return PipelineState(
        state.initiative_id, state.business_id, nxt, _status_for(nxt), reason=f"approved by {actor}"
    )
