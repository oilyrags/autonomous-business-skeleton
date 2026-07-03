"""The growth runner (PRD 0007 E3): drive a created experiment to a deterministic decision.

Pure: assemble the per-arm live conversion stats (from `ab_ads` + MVP funnels) into a control/variant
`Experiment`, then call `ab_growth.decide` — the runner **never** makes the scale/kill call itself
(ADR-0058 decision 2). The experiment's own `budget_minor` is honoured as a spend cap by tightening
the effective experiment budget decide sees, so an experiment that burns its cap concludes rather
than running forever. The impure persist+publish step (`store.conclude`) records the outcome and
publishes `ExperimentConcluded`, which the portfolio context already folds into capital signals.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Decision, Experiment, Variant, decide
from ab_growth.store import ExperimentRecord


@dataclass(frozen=True)
class ArmStats:
    """Live measurement of one arm — impressions, conversions, and spend so far (minor units)."""

    impressions: int
    conversions: int
    spend_minor: int


def assemble(record: ExperimentRecord, control: ArmStats, variant: ArmStats) -> Experiment:
    """Build the control/variant `Experiment` the decision engine scores. Pure."""
    return Experiment(
        experiment_id=record.experiment_id,
        business_id=record.business_id,
        hypothesis=record.hypothesis,
        control=Variant(
            name="control",
            impressions=control.impressions,
            conversions=control.conversions,
            spend_minor=control.spend_minor,
        ),
        variant=Variant(
            name="treatment",
            impressions=variant.impressions,
            conversions=variant.conversions,
            spend_minor=variant.spend_minor,
        ),
    )


def run(record: ExperimentRecord, blueprint: Blueprint, *, control: ArmStats, variant: ArmStats) -> Decision:
    """Assemble the arm stats and let `decide` rule. The experiment's own budget_minor caps the
    effective experiment budget decide sees (never above the blueprint's), so hitting the cap
    concludes the experiment through decide's own budget-exhaustion path."""
    exp = assemble(record, control, variant)
    effective = blueprint.model_copy(
        update={"experiment_budget_minor": min(blueprint.experiment_budget_minor, record.budget_minor)}
    )
    return decide(exp, effective)
