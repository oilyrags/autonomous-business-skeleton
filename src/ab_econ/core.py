"""Per-business unit economics (pure, no I/O, integer minor units).

The deterministic economic signal for a business: is it making money, and how much revenue does
its LLM inference eat? Money stays in integer minor units (like the ledger); ratios are integer
basis points (bps, /10000). Report-only — no ledger writes, no events (feeding the portfolio score
is a follow-up).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    PROFITABLE = "profitable"
    BREAK_EVEN = "break_even"
    UNPROFITABLE = "unprofitable"


class UnitInputs(BaseModel):
    business_id: str
    revenue_minor: int = Field(ge=0)
    cogs_minor: int = Field(ge=0)
    ad_spend_minor: int = Field(ge=0)
    llm_spend_minor: int = Field(ge=0)
    customers: int = Field(ge=0)


@dataclass(frozen=True)
class UnitEconomics:
    business_id: str
    operating_profit_minor: int
    cac_minor: int | None
    gross_margin_bps: int | None
    llm_cost_ratio_bps: int | None
    verdict: Verdict


def economics(inputs: UnitInputs) -> UnitEconomics:
    """Derive unit economics from ledger-shaped per-business inputs."""
    profit = inputs.revenue_minor - inputs.cogs_minor - inputs.ad_spend_minor - inputs.llm_spend_minor
    if profit > 0:
        verdict = Verdict.PROFITABLE
    elif profit == 0:
        verdict = Verdict.BREAK_EVEN
    else:
        verdict = Verdict.UNPROFITABLE
    cac = inputs.ad_spend_minor // inputs.customers if inputs.customers else None
    gross = inputs.revenue_minor - inputs.cogs_minor - inputs.llm_spend_minor
    gross_margin_bps = (gross * 10_000) // inputs.revenue_minor if inputs.revenue_minor else None
    llm_ratio_bps = (
        (inputs.llm_spend_minor * 10_000) // inputs.revenue_minor if inputs.revenue_minor else None
    )
    return UnitEconomics(
        business_id=inputs.business_id,
        operating_profit_minor=profit,
        cac_minor=cac,
        gross_margin_bps=gross_margin_bps,
        llm_cost_ratio_bps=llm_ratio_bps,
        verdict=verdict,
    )


def within_llm_budget(inputs: UnitInputs, *, llm_budget_minor: int) -> bool:
    """Whether a business's LLM inference spend is within its per-business budget.

    A thin, deterministic guard (mirrors ``ab_factory.can_spend``) — the seam a gateway or the
    portfolio can call before authorising further model spend for a business.
    """
    return inputs.llm_spend_minor <= llm_budget_minor
