"""Business Factory demo: provision + gate businesses across a portfolio (infra-free).

    uv run python -m ab_factory

Shows the deterministic instantiation + readiness gate + spend decision, scoped per
business (business_id). Capital allocation is simulated here (cash == capital); the store
does the real ledger allocation.
"""

from __future__ import annotations

from ab_factory.core import Underfunded, activate, can_spend, provision, readiness
from ab_growth.blueprint import Blueprint

BLUEPRINTS = [
    Blueprint(
        business_id="inboxiq",
        name="InboxIQ",
        target_revenue_minor=10_000_00,
        experiment_budget_minor=2_000_00,
        min_conversion_rate=0.04,
        max_cac_minor=50_00,
    ),
    Blueprint(
        business_id="brieflytics",
        name="Brieflytics",
        target_revenue_minor=8_000_00,
        experiment_budget_minor=1_000_00,
        min_conversion_rate=0.06,
        max_cac_minor=30_00,
    ),
]

# (blueprint index, capital, kill_switch_clear, compliance_clear) — the portfolio's provisioning plan.
PLAN = [
    (0, 5_000_00, True, True),  # funded + clean  -> ACTIVE
    (1, 3_000_00, True, False),  # blocked by compliance -> stays DRAFT (capital locked)
]


def main() -> int:
    for idx, capital, ks_clear, comp_clear in PLAN:
        bp = BLUEPRINTS[idx]
        b = provision(bp, capital_minor=capital)  # capital now "allocated" -> cash == capital
        r = readiness(b, cash_balance=capital, kill_switch_clear=ks_clear, compliance_clear=comp_clear)
        activate(b, r)
        print(f"[{b.status.value.upper():6}] {b.business_id:12} capital={b.capital_minor}")
        if not r.ready:
            print(f"           blocked: {', '.join(r.reasons)}")
        else:
            ok = can_spend(b, capital // 2, cash_balance=capital)
            print(f"           can_spend(half runway)? {ok.allowed} — {ok.reason}")

    print("\n== an underfunded provision is refused up front ==")
    try:
        provision(BLUEPRINTS[0], capital_minor=1_000_00)  # below experiment budget 2_000_00
    except Underfunded as exc:
        print(f"  refused: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
