"""Portfolio capital-allocation demo (deterministic, no infra).

    uv run python -m ab_portfolio

The full pipeline: the growth context's ``ExperimentConcluded`` outcomes are rolled up per
business into performance, then allocated a capital action — recycling capital from losers into
winners within the portfolio budget cap. Recommend-only; capital moves are human-in-the-loop.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ab_portfolio.core import allocate
from ab_portfolio.rollup import rollup
from ab_schemas.events import DataClassification, ExperimentConcluded, SubjectRef


def _concluded(business_id: str, action: str, seq: int) -> ExperimentConcluded:
    return ExperimentConcluded(
        event_name="ExperimentConcluded",
        event_id=f"{business_id}-{seq}",
        occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
        producer="growth.experiment_agent",
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="Experiment", id=f"{business_id}-{seq}"),
        business_id=business_id,
        experiment_id=f"{business_id}-{seq}",
        action=action,
        reason="demo",
        p_value=0.01,
        control_rate=0.10,
        variant_rate=0.20,
    )


# As the growth engine would have published them: two winners, a conclusive loser, a marginal
# loser, and a still-inconclusive newcomer (one win + one pivot).
OUTCOMES = [
    *(_concluded("rocket", "scale", i) for i in range(4)),
    *(_concluded("steady", "scale", i) for i in range(2)),
    *(_concluded("sinker", "kill", i) for i in range(3)),
    _concluded("wobble", "kill", 0),
    _concluded("early", "scale", 0),
    _concluded("early", "pivot", 1),
]
# Deployed capital per business (the ledger balance — injected, not derived from events).
CAPITAL_BY_BUSINESS = {
    "rocket": 100_000,
    "steady": 100_000,
    "sinker": 200_000,
    "wobble": 100_000,
    "early": 100_000,
}
PORTFOLIO_BUDGET_MINOR = 500_000  # tight: only one winner's increment of headroom after the reclaim


def main() -> int:
    performances = rollup(OUTCOMES, capital_by_business=CAPITAL_BY_BUSINESS)
    recs = allocate(performances, portfolio_budget_minor=PORTFOLIO_BUDGET_MINOR)
    deployed = sum(p.capital_minor for p in performances)
    for r in recs:
        print(f"  [{r.action.value.upper():11}] {r.business_id:8} Δcapital={r.capital_delta:+8} — {r.reason}")
    net = deployed + sum(r.capital_delta for r in recs)
    within = net <= PORTFOLIO_BUDGET_MINOR
    print(f"\ndeployed {deployed} → {net} (budget {PORTFOLIO_BUDGET_MINOR}); within cap: {within}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
