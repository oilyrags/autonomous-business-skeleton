"""Observability demo (deterministic, no infra).

    uv run python -m ab_obs

Fleet overview + cost attribution + anomaly detection over an in-memory ledger: each business's
revenue/spend is attributed from the ledger, rolled into a health snapshot, and anomalies (LLM cost
too high, operating loss) are flagged. A real tracing/dashboard backend renders on top of this.
"""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger, Posting, Transaction
from ab_obs.core import detect_anomalies, fleet_overview, fleet_totals
from ab_revenue.core import Charge, record_charges
from ab_revenue.gateway import StubRevenueGateway


def _meter(led: InMemoryLedger, bid: str, cost: int, key: str) -> None:
    led.post(
        Transaction(
            key,
            key,
            (Posting(f"{bid}:llm_spend", cost), Posting(f"{bid}:cash", -cost)),
            maker="gateway",
            business_id=bid,
        )
    )


def _seed() -> InMemoryLedger:
    led = InMemoryLedger()
    _meter(led, "rocket", 20_000, "rm")
    _meter(led, "hog", 100_000, "hm1")
    _meter(led, "hog", 100_000, "hm2")
    record_charges(
        StubRevenueGateway(
            [
                Charge(business_id="rocket", amount_minor=1_000_000, customer_ref="c", external_ref="rr"),
                Charge(business_id="hog", amount_minor=250_000, customer_ref="c", external_ref="hr"),
            ]
        ),
        led,
    )
    return led


CONFIGS = {"rocket": (100_000, 100), "hog": (80_000, 40)}  # (cogs, customers)


def main() -> int:
    led = _seed()
    snaps = fleet_overview(led, CONFIGS)
    for s in snaps:
        print(
            f"  {s.business_id:7} revenue={s.revenue_minor:8} llm={s.llm_spend_minor:7} "
            f"profit={s.operating_profit_minor:+8} [{s.verdict.upper()}]"
        )
    t = fleet_totals(snaps)
    print(
        f"\n  FLEET: {t.businesses} businesses, revenue {t.total_revenue_minor}, "
        f"spend {t.total_spend_minor}, profit {t.total_operating_profit_minor:+}, unprofitable {t.unprofitable}"
    )
    print("\n  anomalies:")
    anomalies = detect_anomalies(snaps, max_llm_cost_ratio_bps=2_000, operating_loss_floor_minor=-10_000)
    for a in anomalies:
        print(f"    [{a.kind.value.upper()}] {a.business_id}: {a.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
