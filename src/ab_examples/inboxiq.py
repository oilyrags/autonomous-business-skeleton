"""InboxIQ — one business, end to end, through the real modules (deterministic, no infra).

    uv run python -m ab_examples   ·   ./abctl inboxiq   ·   make inboxiq

The worked example the architecture promises: a fictional B2B SaaS ("AI email triage for busy
founders") is provisioned by the Factory, ships an MVP, markets itself, buys customers, runs
experiments, closes sales, takes money — and the ledger, economics, portfolio, and monitoring all
agree about what happened. Every module here is the real one (stub adapters at the external seams);
nothing is mocked, and every cent is attributable to ``business_id="inboxiq"``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_ads.core import AdCampaign, attributed_cac_minor, run_campaigns
from ab_ads.platform import StubAdPlatform
from ab_econ.core import UnitInputs, economics, profit_and_loss, unprofitable_ids
from ab_factory.core import activate, provision, readiness
from ab_gateway.llm_budget import LLMBudgetExceeded, gate_llm_spend
from ab_growth.blueprint import Blueprint
from ab_growth.experiment import Experiment, Variant, decide, to_event
from ab_ledger.core import InMemoryLedger, Posting, Transaction
from ab_monitor.business import business_checks
from ab_monitor.invariants import ledger_balance_check
from ab_mvp.core import deploy_mvp
from ab_mvp.deployer import StubDeployer
from ab_obs.core import detect_anomalies, snapshot
from ab_portfolio.core import allocate
from ab_portfolio.rollup import rollup
from ab_revenue.core import Charge, record_charges
from ab_revenue.gateway import StubRevenueGateway
from ab_sales.core import Lead, run_pipeline, to_charge
from ab_social.core import plan, publish_content
from ab_social.generator import StubContentGenerator
from ab_social.metrics import PostMetrics, StubMetricsSource, collect_metrics
from ab_social.profile import Pillar, PlatformConfig, PostingRules, SocialProfile
from ab_social.publisher import StubPublisher

BID = "inboxiq"
CAPITAL_MINOR = 500_000
COGS_MINOR = 40_000  # fulfilment cost (hosting, support) — injected until a cogs rail exists
KPI_WEIGHTS = {"engagement_rate": 0.4, "comments_quality": 0.3, "link_clicks": 0.2, "follower_growth": 0.1}

BLUEPRINT = Blueprint(
    business_id=BID,
    name="InboxIQ",
    target_revenue_minor=1_000_000,
    experiment_budget_minor=200_000,
    min_conversion_rate=0.05,
    max_cac_minor=5_000,
    llm_budget_minor=100_000,
    enabled_modules=("waitlist", "checkout"),
)

SOCIAL = SocialProfile(
    business_id=BID,
    voice="Practical, founder-to-founder, zero fluff.",
    pillars=(Pillar(name="Email productivity", weight=0.6), Pillar(name="Founder stories", weight=0.4)),
    platforms=(
        PlatformConfig(name="linkedin", format_mix={"carousel": 0.7, "text_post": 0.3}),
        PlatformConfig(name="x", format_mix={"thread": 0.6, "text_post": 0.4}),
    ),
    posting_rules=PostingRules(
        forbidden=("guaranteed",),
        required_elements=("cta_or_question", "relevant_hashtags_or_keywords"),
    ),
    kpi_weights=KPI_WEIGHTS,
)


@dataclass(frozen=True)
class InboxIQSummary:
    """What the story proved — asserted by the test, printed in the epilogue."""

    activated: bool
    mvp_url: str
    posts_published: int
    ad_cac_minor: int | None
    experiments_scaled: int
    deals_won: int
    revenue_minor: int
    operating_profit_minor: int
    verdict: str
    allocation_action: str
    health_status: str
    llm_denied: bool
    trial_balance: int


def _act(n: int, title: str) -> None:
    print(f"\n=== Act {n} — {title} ===")


def run(*, verbose: bool = True) -> InboxIQSummary:
    led = InMemoryLedger()
    echo = print if verbose else (lambda *_a, **_k: None)

    # Act 1 — the Factory funds and clears the business.
    if verbose:
        _act(1, "provision: Blueprint + capital, behind the readiness gate")
    led.post(
        Transaction(
            "cap-1",
            "cap-1",
            postings=(Posting(f"{BID}:cash", CAPITAL_MINOR), Posting("portfolio:treasury", -CAPITAL_MINOR)),
            maker="executive.portfolio_agent",
            checker="treasury.control_agent",
            business_id=BID,
        )
    )
    business = provision(BLUEPRINT, CAPITAL_MINOR)
    ready = readiness(
        business,
        cash_balance=led.account_balance(f"{BID}:cash"),
        kill_switch_clear=True,
        compliance_clear=True,
    )
    business = activate(business, ready)
    echo(f"  {BID} funded ({CAPITAL_MINOR} minor); ready={ready.ready} -> {business.status.value}")

    # Act 2 — an MVP goes live.
    if verbose:
        _act(2, "MVP: Blueprint -> landing page -> deployed URL")
    deployment, _mvp_event = deploy_mvp(BLUEPRINT, StubDeployer())
    echo(f"  deployed {deployment.url} (page {deployment.content_hash[:12]}…)")

    # Act 3 — marketing publishes on-brand content (QA-gated), and it gets measured.
    if verbose:
        _act(3, "marketing: plan -> generate -> QA -> publish -> score")
    generator, publisher = StubContentGenerator(), StubPublisher()
    published = []
    for item in plan(SOCIAL, count=3):
        event = publish_content(generator.write(item, SOCIAL), SOCIAL, publisher)
        if event is not None:
            published.append(event)
            echo(f"  [PUBLISH] {event.platform:8} {event.pillar:18} -> {event.platform_post_id}")
    first_post = published[0].platform_post_id
    metrics_src = StubMetricsSource(
        {
            first_post: PostMetrics(
                business_id=BID,
                platform_post_id=first_post,
                impressions=1_000,
                likes=70,
                comments=20,
                shares=10,
                clicks=25,
                follows=8,
            )
        }
    )
    scored = collect_metrics(first_post, metrics_src, KPI_WEIGHTS)
    echo(f"  {first_post}: composite engagement {scored.composite_score_bps} bps")

    # Act 4 — paid acquisition, spend on the ledger, CAC from real conversions.
    if verbose:
        _act(4, "acquisition: ad spend -> ledger, conversions -> CAC")
    platform = StubAdPlatform(cost_per_conversion_minor=3_000)
    campaign = AdCampaign(business_id=BID, spend_minor=60_000, channel="linkedin", external_ref="iq-ads-1")
    run_campaigns(platform, [campaign], led)
    cac = attributed_cac_minor(platform.run(campaign))
    echo(f"  spent 60000 on linkedin -> 20 conversions, CAC={cac} (ceiling {BLUEPRINT.max_cac_minor})")

    # Act 5 — experiments decide, with statistics.
    if verbose:
        _act(5, "experiments: two significant wins -> SCALE")
    experiment_events = []
    for i, hypothesis in enumerate(("landing headline v2 converts better", "pricing page trial CTA wins"), 1):
        exp = Experiment(
            experiment_id=f"iq-exp-{i}",
            business_id=BID,
            hypothesis=hypothesis,
            control=Variant(name="control", impressions=1_000, conversions=40, spend_minor=30_000),
            variant=Variant(name="variant", impressions=1_000, conversions=120, spend_minor=30_000),
        )
        decision = decide(exp, BLUEPRINT)
        experiment_events.append(to_event(exp, decision))
        echo(f"  {exp.experiment_id}: {decision.action.value.upper()} (p={decision.p_value:.4f})")

    # Act 6 — sales closes; won deals become charges. The waitlist converts too.
    if verbose:
        _act(6, "sales: qualify -> close; won deals + subscriptions become charges")
    leads = [
        Lead(
            business_id=BID, opportunity_id="iq-op1", fit_score=80, budget_minor=120_000, amount_minor=90_000
        ),
        Lead(
            business_id=BID, opportunity_id="iq-op2", fit_score=70, budget_minor=80_000, amount_minor=60_000
        ),
        Lead(
            business_id=BID, opportunity_id="iq-op3", fit_score=20, budget_minor=200_000, amount_minor=50_000
        ),
    ]
    charges: list[Charge] = []
    won = 0
    for lead in leads:
        result = run_pipeline(lead, min_fit_score=50, min_budget_minor=10_000)
        echo(f"  {result.opportunity_id} [{result.stage.value.upper():4}] {result.reason}")
        charge = to_charge(result)
        if charge is not None:
            charges.append(charge)
            won += 1
    charges += [
        Charge(business_id=BID, amount_minor=5_000, customer_ref=f"waitlist-{n}", external_ref=f"iq-sub-{n}")
        for n in range(1, 21)  # 20 subscriptions from the MVP waitlist
    ]

    # Act 7 — money: revenue booked; LLM inference metered and BUDGET-GATED.
    if verbose:
        _act(7, "money: revenue -> ledger; LLM spend metered, over-budget call refused")
    record_charges(StubRevenueGateway(charges), led)
    llm_spent = 0
    for cost in (20_000, 15_000):
        gate_llm_spend(BID, cost_minor=cost, spent_minor=llm_spent, budget_minor=BLUEPRINT.llm_budget_minor)
        led.post(
            Transaction(
                f"llm-{cost}",
                f"llm-{cost}",
                postings=(Posting(f"{BID}:llm_spend", cost), Posting(f"{BID}:cash", -cost)),
                maker="gateway",
                business_id=BID,
            )
        )
        llm_spent += cost
    llm_denied = False
    try:
        gate_llm_spend(BID, cost_minor=70_000, spent_minor=llm_spent, budget_minor=BLUEPRINT.llm_budget_minor)
    except LLMBudgetExceeded as exc:
        llm_denied = True
        echo(f"  [DENIED before inference] {exc}")
    echo(f"  revenue booked: {led.business_revenue(BID)}; llm metered: {llm_spent}")

    # Act 8 — economics, from the ledger.
    if verbose:
        _act(8, "economics: the ledger decides whether InboxIQ makes money")
    spend = led.business_spend(BID)
    inputs = UnitInputs(
        business_id=BID,
        revenue_minor=led.business_revenue(BID),
        cogs_minor=COGS_MINOR,
        ad_spend_minor=spend.external_spend_minor,
        llm_spend_minor=spend.llm_spend_minor,
        customers=22,  # 2 closed deals + 20 subscriptions
    )
    econ = economics(inputs, expected_lifetime_periods=12)
    pnl = profit_and_loss(inputs)
    echo(
        f"  revenue={pnl.revenue_minor} gross={pnl.gross_profit_minor} "
        f"contribution={pnl.contribution_margin_minor} operating={pnl.operating_profit_minor}"
    )
    verdict_tag = econ.verdict.value.upper()
    echo(f"  CAC={econ.cac_minor} LTV={econ.ltv_minor} payback={econ.payback_periods} -> [{verdict_tag}]")

    # Act 9 — the portfolio reacts to real outcomes + real money.
    if verbose:
        _act(9, "portfolio: experiment wins + profitability -> capital follows")
    perfs = rollup(experiment_events, capital_by_business={BID: CAPITAL_MINOR})
    losers = unprofitable_ids([econ])
    rec = allocate(perfs, portfolio_budget_minor=1_000_000, unprofitable_business_ids=losers)[0]
    echo(f"  allocation: {rec.action.value.upper()} ({rec.reason}) Δcapital={rec.capital_delta:+}")

    # Act 10 — the watchtower agrees.
    if verbose:
        _act(10, "watchtower: obs + monitor + the ledger invariant")
    snap = snapshot(led, BID, cogs_minor=COGS_MINOR, customers=22)
    anomalies = detect_anomalies([snap], max_llm_cost_ratio_bps=2_000, operating_loss_floor_minor=-10_000)
    (health,) = business_checks([snap], anomalies)
    balance = ledger_balance_check(trial_balance=led.trial_balance())
    echo(f"  {health.render()}")
    echo(f"  {balance.render()}")

    return InboxIQSummary(
        activated=business.status.value == "active",
        mvp_url=deployment.url,
        posts_published=len(published),
        ad_cac_minor=cac,
        experiments_scaled=sum(1 for e in experiment_events if e.action == "scale"),
        deals_won=won,
        revenue_minor=led.business_revenue(BID),
        operating_profit_minor=econ.operating_profit_minor,
        verdict=econ.verdict.value,
        allocation_action=rec.action.value,
        health_status=health.status.name,
        llm_denied=llm_denied,
        trial_balance=led.trial_balance(),
    )


def main() -> int:
    summary = run()
    print("\n=== Epilogue ===")
    print(f"  activated={summary.activated}  mvp={summary.mvp_url}")
    print(
        f"  posts={summary.posts_published}  CAC={summary.ad_cac_minor}  "
        f"scaled={summary.experiments_scaled}  won={summary.deals_won}"
    )
    print(
        f"  revenue={summary.revenue_minor}  profit={summary.operating_profit_minor:+}  "
        f"[{summary.verdict.upper()}]"
    )
    print(f"  portfolio says: {summary.allocation_action.upper()}  ·  health: {summary.health_status}")
    print(f"  over-budget LLM call refused: {summary.llm_denied}  ·  trial balance: {summary.trial_balance}")
    print(f"\n  one business, every context, no infrastructure — all attributable to business_id={BID!r}.")
    ok = (
        summary.activated
        and summary.verdict == "profitable"
        and summary.health_status == "OK"
        and summary.trial_balance == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
