"""Experimentation & Growth demo: run experiments for two businesses through the engine.

    uv run python -m ab_growth

Shows the deterministic scale/pivot/kill/continue decision on evidence + guardrails, scoped
per business (business_id). No infra.
"""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Experiment, Variant, decide

# Two businesses in the portfolio, each with its own budget, KPI, and guardrails.
BLUEPRINTS = {
    "inboxiq": Blueprint(
        business_id="inboxiq",
        name="InboxIQ — AI email triage for SMB support",
        target_revenue_minor=10_000_00,
        experiment_budget_minor=2_000_00,
        min_conversion_rate=0.04,
        max_cac_minor=50_00,
    ),
    "brieflytics": Blueprint(
        business_id="brieflytics",
        name="Brieflytics — AI meeting briefs",
        target_revenue_minor=8_000_00,
        experiment_budget_minor=1_000_00,
        min_conversion_rate=0.06,
        max_cac_minor=30_00,
    ),
}

# (business, hypothesis, control(imp,conv,spend_cents), variant(imp,conv,spend_cents))
CASES = [
    ("inboxiq", "value-prop headline lifts signups", (2000, 60, 800_00), (2000, 130, 900_00)),
    ("inboxiq", "aggressive discount burns CAC", (2000, 60, 800_00), (2000, 12, 900_00)),
    ("inboxiq", "real lift but still below the KPI", (5000, 100, 800_00), (5000, 175, 900_00)),
    ("inboxiq", "flashy redesign hurts conversion", (3000, 180, 800_00), (3000, 90, 900_00)),
    ("brieflytics", "early read, too few samples", (200, 12, 200_00), (200, 16, 250_00)),
    ("brieflytics", "inconclusive and out of budget", (800, 20, 500_00), (800, 26, 600_00)),
]


def main() -> int:
    for biz, hypothesis, ctrl, var in CASES:
        bp = BLUEPRINTS[biz]
        exp = Experiment(
            experiment_id=f"exp_{biz}_{abs(hash(hypothesis)) % 10000}",
            business_id=biz,
            hypothesis=hypothesis,
            control=Variant(name="control", impressions=ctrl[0], conversions=ctrl[1], spend_minor=ctrl[2]),
            variant=Variant(name="variant", impressions=var[0], conversions=var[1], spend_minor=var[2]),
        )
        dec = decide(exp, bp)
        print(f"[{dec.action.value.upper():8}] {biz:12} {hypothesis!r}")
        print(f"           {dec.reason} | lift {dec.lift:+.3f}, p={dec.p_value:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
