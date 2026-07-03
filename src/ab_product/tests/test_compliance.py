"""The DPIA compliance gate (PRD 0008 P7): an initiative that processes personal data cannot reach
launch until the human DPIA sign-off is recorded (the instantiation guide's human gate 7). Pure."""

from __future__ import annotations

from ab_product.compliance import clear_dpia, requires_dpia
from ab_product.pipeline import PipelineState, Stage
from ab_schemas.models import ProductInitiative


def _at_dpia(initiative_id: str = "i1") -> PipelineState:
    return PipelineState(initiative_id, "biz", Stage.DPIA, "awaiting_human")


def test_requires_dpia_flags_personal_data_initiatives() -> None:
    assert requires_dpia(ProductInitiative(initiative_id="a", title="x", key_features=["customer profiling"]))
    assert requires_dpia(ProductInitiative(initiative_id="b", title="AI email triage")) is True  # email
    assert (
        requires_dpia(ProductInitiative(initiative_id="c", title="Faster CI cache", key_features=["speed"]))
        is False
    )


def test_a_personal_data_initiative_is_blocked_at_dpia_until_signed() -> None:
    init = ProductInitiative(initiative_id="i1", title="triage", key_features=["process customer emails"])

    blocked = clear_dpia(_at_dpia(), init)  # no approver
    assert blocked.stage is Stage.DPIA and blocked.status == "awaiting_human"  # cannot reach launch

    signed = clear_dpia(_at_dpia(), init, approver="dpo")
    assert signed.stage is Stage.BLUEPRINT and "dpo" in signed.reason  # DPIA recorded → advances


def test_a_non_personal_data_initiative_auto_clears_dpia() -> None:
    init = ProductInitiative(initiative_id="i2", title="Faster CI cache", key_features=["speed up builds"])
    cleared = clear_dpia(_at_dpia("i2"), init)  # no human needed
    assert cleared.stage is Stage.BLUEPRINT and cleared.status == "in_progress"
