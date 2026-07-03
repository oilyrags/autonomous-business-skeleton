"""The DPIA compliance gate for Product Engineering (PRD 0008 P7).

An initiative that processes personal data triggers a Data Protection Impact Assessment: it cannot
pass the DPIA stage — and therefore cannot reach launch — until a human DPIA sign-off is recorded
(the instantiation guide's human gate 7; the `ab_compliance` RoPA / lawful-basis concern). An
initiative with no personal data auto-clears the DPIA stage deterministically. Pure.
"""

from __future__ import annotations

from ab_product.pipeline import PipelineState, Stage, approve_human
from ab_schemas.models import ProductInitiative

# Personal-data signals that trigger a DPIA (the CLO/DPO concern; a real deployment consults the
# ab_compliance RoPA + data-inventory `08` records).
_PERSONAL_DATA_SIGNALS = frozenset(
    {
        "personal",
        "pii",
        "email",
        "customer",
        "profiling",
        "health",
        "biometric",
        "identity",
        "location",
        "behaviour",
    }
)


def requires_dpia(initiative: ProductInitiative) -> bool:
    """True iff the initiative processes personal data (→ a DPIA is required before launch)."""
    haystack = " ".join(
        [initiative.title, initiative.hypothesis, *initiative.key_features, *initiative.constraints]
    ).lower()
    return any(signal in haystack for signal in _PERSONAL_DATA_SIGNALS)


def clear_dpia(
    state: PipelineState, initiative: ProductInitiative, *, approver: str | None = None
) -> PipelineState:
    """Resolve the DPIA stage. No personal data → auto-clear (deterministic). Personal data → requires
    a recorded human sign-off: with an `approver` it advances; without one it stays blocked
    (awaiting_human), so a personal-data product can never reach launch un-assessed."""
    if state.stage is not Stage.DPIA:
        raise ValueError(f"not at the DPIA gate (stage {state.stage})")
    if not requires_dpia(initiative):
        return PipelineState(
            state.initiative_id, state.business_id, Stage.BLUEPRINT, "in_progress", reason="no DPIA required"
        )
    if approver is None:
        return state  # blocked: personal data needs a human DPIA sign-off before launch
    return approve_human(state, actor=f"DPIA:{approver}")
