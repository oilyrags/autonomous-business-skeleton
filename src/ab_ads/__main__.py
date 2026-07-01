"""Paid-acquisition demo (deterministic, no infra).

    uv run python -m ab_ads

Two businesses run ad campaigns through the (stub) platform; spend is booked to the ledger and
conversions come back, so CAC is real. A real Meta/Google Ads adapter slots in behind the port.
"""

from __future__ import annotations

from ab_ads.core import AdCampaign, attributed_cac_minor, run_campaigns
from ab_ads.platform import StubAdPlatform
from ab_ledger.core import InMemoryLedger

CAMPAIGNS = [
    AdCampaign(business_id="rocket", spend_minor=100_000, channel="meta", external_ref="c1"),
    AdCampaign(business_id="steady", spend_minor=60_000, channel="google", external_ref="c2"),
]


def main() -> int:
    led = InMemoryLedger()
    platform = StubAdPlatform(cost_per_conversion_minor=2_500)
    events = run_campaigns(platform, CAMPAIGNS, led)
    for e in events:
        result = platform.run(next(c for c in CAMPAIGNS if c.external_ref == e.external_ref))
        cac = attributed_cac_minor(result)
        print(
            f"  {e.business_id:7} {e.channel:7} spend={e.spend_minor:6} "
            f"conversions={e.conversions:3} CAC={cac}"
        )
    print()
    for bid in ("rocket", "steady"):
        print(f"  {bid:7} ledger ad spend: {led.business_spend(bid).external_spend_minor}")
    print(f"\ntrial balance: {led.trial_balance()} (money conserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
