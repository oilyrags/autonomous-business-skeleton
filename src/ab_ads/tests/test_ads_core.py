"""Paid acquisition: campaigns spend real ledger money and attribute conversions (pure, infra-free)."""

from __future__ import annotations

from ab_ads.core import AdCampaign, attributed_cac_minor, run_campaigns, to_transaction
from ab_ads.platform import StubAdPlatform
from ab_ledger.core import InMemoryLedger


def _campaign(bid: str = "acme", spend: int = 100_000, *, ref: str = "c1") -> AdCampaign:
    return AdCampaign(business_id=bid, spend_minor=spend, channel="meta", external_ref=ref)


def test_stub_platform_converts_spend_at_cost_per_conversion() -> None:
    result = StubAdPlatform(cost_per_conversion_minor=2_000).run(_campaign(spend=100_000))
    assert result.conversions == 50  # 100_000 / 2_000


def test_attributed_cac_is_spend_per_conversion() -> None:
    result = StubAdPlatform(cost_per_conversion_minor=2_000).run(_campaign(spend=100_000))
    assert attributed_cac_minor(result) == 2_000  # 100_000 / 50


def test_ad_spend_books_to_the_ledger_as_business_scoped_outflow() -> None:
    led = InMemoryLedger()
    result = StubAdPlatform(cost_per_conversion_minor=2_000).run(_campaign("acme", 40_000))
    led.post(to_transaction(result, maker="growth.ad_agent", checker="treasury.control_agent"))
    # The ad spend shows up as this business's external spend (feeds ab_econ CAC).
    assert led.business_spend("acme").external_spend_minor == 40_000
    assert led.account_balance("acme:cash") == -40_000  # money left to the ad platform
    assert led.trial_balance() == 0


def test_run_campaigns_books_and_emits_per_campaign() -> None:
    led = InMemoryLedger()
    platform = StubAdPlatform(cost_per_conversion_minor=1_000)
    events = run_campaigns(
        platform,
        [_campaign("acme", 30_000, ref="a1"), _campaign("beta", 50_000, ref="b1")],
        led,
    )
    assert [(e.business_id, e.conversions) for e in events] == [("acme", 30), ("beta", 50)]
    assert led.business_spend("acme").external_spend_minor == 30_000
    assert led.business_spend("beta").external_spend_minor == 50_000
    assert led.trial_balance() == 0
