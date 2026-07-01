"""Per-business LLM budget enforcement demo (deterministic, no infra).

    uv run python -m ab_gateway.llm_budget_demo

Runs the pure gate over a sequence of model calls for one business: spend accumulates with each
call until the next would breach the budget, at which point the gate refuses it *before* any
inference. Mirrors what the gateway does live (metering the spend in the ledger).
"""

from __future__ import annotations

from ab_gateway.llm_budget import LLMBudgetExceeded, gate_llm_spend

BUSINESS_ID = "acme"
BUDGET_MINOR = 50_000
COST_PER_CALL_MINOR = 12_000


def main() -> int:
    spent = 0
    for i in range(1, 6):
        try:
            gate_llm_spend(
                BUSINESS_ID,
                cost_minor=COST_PER_CALL_MINOR,
                spent_minor=spent,
                budget_minor=BUDGET_MINOR,
            )
        except LLMBudgetExceeded as exc:
            print(f"  call {i}: DENIED before inference — {exc}")
            print(f"\nbudget {BUDGET_MINOR} held: spent {spent}, refused call {i} (+{COST_PER_CALL_MINOR})")
            return 0
        spent += COST_PER_CALL_MINOR  # the live path meters this to {business}:llm_spend
        print(f"  call {i}: allowed — cumulative LLM spend now {spent}/{BUDGET_MINOR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
