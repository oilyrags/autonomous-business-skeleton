"""Observability: cost attribution, fleet overview, anomaly detection over the ledger (pure)."""

from __future__ import annotations

from ab_ledger.core import InMemoryLedger, Posting, Transaction
from ab_obs.core import AnomalyKind, detect_anomalies, fleet_overview, fleet_totals, snapshot
from ab_revenue.core import Charge, record_charges
from ab_revenue.gateway import StubRevenueGateway


def _seed() -> InMemoryLedger:
    led = InMemoryLedger()
    # rocket: healthy — 1M revenue, modest spend.
    led.post(
        Transaction(
            "rm",
            "rm",
            (Posting("rocket:llm_spend", 20_000), Posting("rocket:cash", -20_000)),
            maker="g",
            business_id="rocket",
        )
    )
    # hog: bleeding — thin revenue, heavy llm.
    led.post(
        Transaction(
            "hm1",
            "hm1",
            (Posting("hog:llm_spend", 100_000), Posting("hog:cash", -100_000)),
            maker="g",
            business_id="hog",
        )
    )
    led.post(
        Transaction(
            "hm2",
            "hm2",
            (Posting("hog:llm_spend", 100_000), Posting("hog:cash", -100_000)),
            maker="g",
            business_id="hog",
        )
    )
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
# hog: revenue 250k − cogs 80k − llm 200k = −30k operating loss (unprofitable)


def test_snapshot_attributes_revenue_and_spend_from_the_ledger() -> None:
    s = snapshot(_seed(), "rocket", cogs_minor=100_000, customers=100)
    assert s.revenue_minor == 1_000_000
    assert s.llm_spend_minor == 20_000
    # 1_000_000 − 100_000 cogs − 0 ad − 20_000 llm = 880_000
    assert s.operating_profit_minor == 880_000
    assert s.verdict == "profitable"


def test_fleet_totals_aggregate_the_portfolio() -> None:
    totals = fleet_totals(fleet_overview(_seed(), CONFIGS))
    assert totals.businesses == 2
    assert totals.total_revenue_minor == 1_250_000  # 1_000_000 + 250_000
    assert totals.total_spend_minor == 220_000  # rocket 20k llm + hog 200k llm
    assert totals.unprofitable == 1  # hog


def test_anomaly_detection_flags_high_llm_cost_and_losses() -> None:
    snaps = fleet_overview(_seed(), CONFIGS)
    anomalies = detect_anomalies(snaps, max_llm_cost_ratio_bps=2_000, operating_loss_floor_minor=-10_000)
    kinds = {(a.business_id, a.kind) for a in anomalies}
    # hog: llm 200k / 250k revenue = 8000bps > 2000; and it's loss-making beyond the floor.
    assert ("hog", AnomalyKind.LLM_COST_HIGH) in kinds
    assert ("hog", AnomalyKind.OPERATING_LOSS) in kinds
    # rocket is healthy — no anomalies.
    assert not any(a.business_id == "rocket" for a in anomalies)
