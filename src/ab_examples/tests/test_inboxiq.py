"""The InboxIQ worked example: one business through every context, with the outcomes pinned."""

from __future__ import annotations

from ab_examples.inboxiq import main, run


def test_the_story_holds_together() -> None:
    s = run(verbose=False)
    assert s.activated is True  # the readiness gate cleared it
    assert s.mvp_url == "https://inboxiq.mvp.stub.local/"
    assert s.posts_published == 3  # QA passed all planned posts
    assert s.ad_cac_minor == 3_000  # 60_000 spend / 20 conversions, under the 5_000 ceiling
    assert s.experiments_scaled == 2  # both wins significant
    assert s.deals_won == 2  # the low-fit lead was qualified out
    assert s.revenue_minor == 250_000  # 90_000 + 60_000 deals + 20 × 5_000 subscriptions
    # 250_000 − 40_000 cogs − 60_000 ads − 35_000 llm = 115_000
    assert s.operating_profit_minor == 115_000
    assert s.verdict == "profitable"
    assert s.allocation_action == "invest_more"  # two scales + profitable -> capital follows
    assert s.health_status == "OK"
    assert s.llm_denied is True  # the over-budget inference call was refused
    assert s.trial_balance == 0  # money conserved across the whole story


def test_the_cli_exits_zero() -> None:
    assert main() == 0
