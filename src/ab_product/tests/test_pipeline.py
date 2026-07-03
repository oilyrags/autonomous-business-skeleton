"""The gated SDLC state machine (PRD 0008 P2): a promoted initiative advances intake → … → launched
through deterministic gates, pausing at the human DPIA + launch gates; a failed gate halts it. Pure."""

from __future__ import annotations

import pytest

from ab_product.compliance import clear_dpia
from ab_product.pipeline import GateResult, Stage, advance, approve_human, start
from ab_schemas.models import ProductInitiative

_OK = GateResult(ok=True)


def test_a_conformant_initiative_advances_with_human_pauses() -> None:
    initiative = ProductInitiative(initiative_id="init-1", title="Vehicle Twin")
    state = start("init-1", "vehicle-twin")
    assert state.stage is Stage.INTAKE and state.status == "in_progress"

    state = advance(state, _OK)  # → spec
    state = advance(state, _OK)  # → design
    state = advance(state, _OK)  # → dpia (human gate)
    assert state.stage is Stage.DPIA and state.status == "awaiting_human"

    state = clear_dpia(state, initiative)  # DPIA resolved through the compliance gate (auto-clears)
    assert state.stage is Stage.BLUEPRINT and state.status == "in_progress"

    state = advance(state, _OK)  # → scaffold
    state = advance(state, _OK)  # → qa
    state = advance(state, _OK)  # → launch (human gate)
    assert state.stage is Stage.LAUNCH and state.status == "awaiting_human"

    state = approve_human(state, actor="ceo")  # launch approved
    assert state.stage is Stage.LAUNCHED and state.status == "launched"


def test_the_dpia_gate_cannot_be_resolved_by_a_plain_human_approval() -> None:
    # approve_human is the generic human-gate primitive; the DPIA gate is NOT plain — it must run the
    # compliance check, so it can only be resolved via clear_dpia (else a personal-data initiative
    # could be waved through without an assessment).
    state = start("init-x", "biz")
    state = advance(advance(advance(state, _OK), _OK), _OK)  # → dpia (awaiting_human)
    with pytest.raises(ValueError, match="clear_dpia"):
        approve_human(state, actor="operator")


def test_a_failed_gate_halts_the_initiative() -> None:
    state = advance(start("init-2", "biz"), GateResult(ok=False, reason="charter conformance failed"))
    assert state.status == "halted" and "conformance" in state.reason
    with pytest.raises(ValueError, match="cannot advance"):
        advance(state, _OK)  # a halted initiative does not advance


def test_a_human_stage_cannot_be_gate_advanced() -> None:
    state = start("init-3", "biz")
    state = advance(advance(advance(state, _OK), _OK), _OK)  # → dpia (awaiting_human)
    with pytest.raises(ValueError):
        advance(state, _OK)  # must be approved by a human, not a deterministic gate
