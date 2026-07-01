"""Business Blueprint — the per-business instantiation config (multi-tenancy: business_id).

A blueprint is how a new business is defined and later instantiated: its identity, its
experiment budget, its success KPI, and the guardrails an experiment must respect. The growth
engine reads it to decide scale/pivot/kill; the same `business_id` scopes events + data so
many businesses run side by side.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Blueprint(BaseModel):
    business_id: str
    name: str
    # Economics (minor units, e.g. cents). experiment_budget caps total spend across an arm-pair.
    target_revenue_minor: int = Field(ge=0)
    experiment_budget_minor: int = Field(gt=0)
    # Success KPI: the variant must reach at least this conversion rate to SCALE.
    min_conversion_rate: float = Field(gt=0, le=1)
    # Guardrail: cost-per-acquisition ceiling (minor units). Breach forces KILL.
    max_cac_minor: int = Field(gt=0)
    # Statistical rigor.
    significance_alpha: float = Field(default=0.05, gt=0, lt=1)
    min_exposure_per_arm: int = Field(default=1000, ge=1)
    enabled_modules: tuple[str, ...] = ()
