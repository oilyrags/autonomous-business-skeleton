"""Per-business LLM budget enforcement (pure, no I/O).

The deterministic gate that makes ``ab_econ.within_llm_budget`` live: a business-scoped model call
is refused *before* it happens once the business's cumulative LLM inference spend would breach its
budget. Spend is metered elsewhere (the ledger cost account); this module only decides.
"""

from __future__ import annotations

from ab_econ.core import UnitInputs, within_llm_budget


class LLMBudgetExceeded(Exception):
    """A business-scoped model call would push cumulative LLM spend past its budget."""

    def __init__(self, business_id: str, spent_minor: int, cost_minor: int, budget_minor: int) -> None:
        self.business_id = business_id
        self.spent_minor = spent_minor
        self.cost_minor = cost_minor
        self.budget_minor = budget_minor
        super().__init__(
            f"business '{business_id}': LLM spend {spent_minor}+{cost_minor} "
            f"would exceed budget {budget_minor}"
        )


def gate_llm_spend(business_id: str, *, cost_minor: int, spent_minor: int, budget_minor: int) -> None:
    """Raise ``LLMBudgetExceeded`` if this call's cost would breach the per-business LLM budget.

    Reuses ``ab_econ.within_llm_budget`` on the *projected* cumulative spend, so the gateway and the
    economics context agree on one definition of "within budget".
    """
    projected = spent_minor + cost_minor
    probe = UnitInputs(
        business_id=business_id,
        revenue_minor=0,
        cogs_minor=0,
        ad_spend_minor=0,
        llm_spend_minor=projected,
        customers=0,
    )
    if not within_llm_budget(probe, llm_budget_minor=budget_minor):
        raise LLMBudgetExceeded(business_id, spent_minor, cost_minor, budget_minor)
