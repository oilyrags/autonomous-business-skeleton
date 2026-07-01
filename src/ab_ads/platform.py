"""The ad-platform port: a paid-acquisition channel (Google/Meta/TikTok Ads) as a swappable seam.
The stub converts spend to attributed conversions at a fixed cost-per-conversion; a real adapter
calling the platform's API implements the same ``run`` — callers never change.
"""

from __future__ import annotations

from typing import Protocol

from ab_ads.core import AdCampaign, AdResult


class AdPlatform(Protocol):
    """Run a campaign: place the spend, return the attributed conversions."""

    def run(self, campaign: AdCampaign) -> AdResult: ...


class StubAdPlatform:
    """Deterministic ad platform: ``conversions = spend // cost_per_conversion``. A real adapter
    (Meta/Google Ads) implements the same ``run`` against the platform API + conversion pixel."""

    def __init__(self, cost_per_conversion_minor: int) -> None:
        if cost_per_conversion_minor <= 0:
            raise ValueError("cost_per_conversion_minor must be positive")
        self._cpc = cost_per_conversion_minor

    def run(self, campaign: AdCampaign) -> AdResult:
        return AdResult(
            business_id=campaign.business_id,
            channel=campaign.channel,
            spend_minor=campaign.spend_minor,
            conversions=campaign.spend_minor // self._cpc,
            external_ref=campaign.external_ref,
        )
