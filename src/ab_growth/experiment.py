"""The experiment decision engine: given an A/B experiment's evidence and a business blueprint,
decide SCALE / PIVOT / KILL / CONTINUE. Deterministic and evidence-based — an agent proposes
the experiment and reads the recommendation, but never overrides the money/guardrail logic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from ab_growth.blueprint import Blueprint
from ab_growth.stats import significant, two_proportion_p_value
from ab_schemas.events import DataClassification, ExperimentConcluded, SubjectRef


class Action(StrEnum):
    SCALE = "scale"  # significant win that meets the success KPI → invest more
    PIVOT = "pivot"  # a real, significant lift but still short of the KPI → iterate
    KILL = "kill"  # guardrail breached, significantly worse, or inconclusive & out of budget
    CONTINUE = "continue"  # underpowered but within budget → gather more data


class Variant(BaseModel):
    name: str
    impressions: int = Field(ge=0)
    conversions: int = Field(ge=0)
    spend_minor: int = Field(ge=0)

    @model_validator(mode="after")
    def _conversions_le_impressions(self) -> Variant:
        if self.conversions > self.impressions:
            raise ValueError("conversions cannot exceed impressions")
        return self

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions else 0.0

    @property
    def cac_minor(self) -> int | None:
        """Cost per acquisition; None when there are no conversions yet (undefined)."""
        return self.spend_minor // self.conversions if self.conversions else None


class Experiment(BaseModel):
    experiment_id: str
    business_id: str
    hypothesis: str
    control: Variant
    variant: Variant

    @property
    def total_spend_minor(self) -> int:
        return self.control.spend_minor + self.variant.spend_minor


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    p_value: float
    lift: float  # variant conversion_rate − control conversion_rate
    evidence: dict[str, Any] = field(default_factory=dict)


def decide(exp: Experiment, bp: Blueprint) -> Decision:
    """Decide the experiment's fate. Guardrails first (hard stops), then statistical evidence."""
    v, c = exp.variant, exp.control
    p_value = two_proportion_p_value(c.conversions, c.impressions, v.conversions, v.impressions)
    lift = v.conversion_rate - c.conversion_rate
    evidence = {
        "control_rate": c.conversion_rate,
        "variant_rate": v.conversion_rate,
        "variant_cac_minor": v.cac_minor,
        "total_spend_minor": exp.total_spend_minor,
        "budget_minor": bp.experiment_budget_minor,
    }

    def d(action: Action, reason: str) -> Decision:
        return Decision(action, reason, p_value, lift, evidence)

    # 1. Guardrail: a real CAC above the ceiling is a hard KILL, regardless of significance.
    if v.cac_minor is not None and v.cac_minor > bp.max_cac_minor:
        return d(Action.KILL, f"CAC {v.cac_minor} > ceiling {bp.max_cac_minor}")

    is_sig = significant(
        c.conversions,
        c.impressions,
        v.conversions,
        v.impressions,
        alpha=bp.significance_alpha,
        min_exposure=bp.min_exposure_per_arm,
    )

    # 2. Statistically conclusive.
    if is_sig:
        if lift <= 0:
            return d(Action.KILL, f"variant significantly worse (p={p_value:.4f})")
        if v.conversion_rate >= bp.min_conversion_rate:
            return d(
                Action.SCALE, f"significant win meeting KPI (rate {v.conversion_rate:.3f}, p={p_value:.4f})"
            )
        return d(Action.PIVOT, f"significant lift but below KPI {bp.min_conversion_rate:.3f} (iterate)")

    # 3. Inconclusive: keep going if we can still afford it, else stop.
    if exp.total_spend_minor >= bp.experiment_budget_minor:
        return d(Action.KILL, "inconclusive and experiment budget exhausted")
    return d(Action.CONTINUE, "underpowered — within budget, gather more data")


def to_event(
    exp: Experiment, decision: Decision, producer: str = "growth.experiment_agent"
) -> ExperimentConcluded:
    """Build the business-scoped domain event for a decision (for publishing on the bus)."""
    return ExperimentConcluded(
        event_name="ExperimentConcluded",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="Experiment", id=exp.experiment_id),
        business_id=exp.business_id,
        experiment_id=exp.experiment_id,
        action=decision.action.value,
        reason=decision.reason,
        p_value=decision.p_value,
        control_rate=exp.control.conversion_rate,
        variant_rate=exp.variant.conversion_rate,
    )
