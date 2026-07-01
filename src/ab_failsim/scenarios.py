"""Failure-injection scenarios from architecture/16. Each returns a ScenarioResult; the
suite passes if every non-deferred scenario is CONTAINED. Deterministic, no infra: it drives
the real control code (eval gate, tool registry, ledger, freshness) with injected failures.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ab_compliance.dsar import erasure_plan
from ab_data.freshness import Freshness, readiness
from ab_evals.gate import evaluate_and_gate
from ab_evals.models import HallucinatingModel
from ab_evals.suites import SIGNIFICANT_CUSTOMER_DECISION
from ab_gateway import tools
from ab_ledger.core import ApprovalRequired, InMemoryLedger, Posting, Transaction, requires_approval, validate
from ab_ops.reliability import ErrorBudget, Incident, ReleaseManager, Severity, handle_incident


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    control: str
    contained: bool
    detail: str
    deferred: bool = False


def _raises(exc: type[Exception], fn: Callable[[], object]) -> bool:
    try:
        fn()
        return False
    except exc:
        return True


def _pay(tid: str, amount: int, maker: str = "cfo_agent", **kw: object) -> Transaction:
    postings = (Posting("counterparty", amount), Posting("cash", -amount))
    return Transaction(tid, f"k{tid}", postings, maker=maker, **kw)  # type: ignore[arg-type]


def bad_model_output() -> ScenarioResult:
    """Hallucinated number in a forecast → eval gate blocks it; ledger math stays deterministic."""
    d = evaluate_and_gate(HallucinatingModel(), SIGNIFICANT_CUSTOMER_DECISION)
    contained = not d.promoted  # blocked by the grounding gate; its output can never serve
    return ScenarioResult(
        "bad_model_output",
        "11/AM-12",
        contained,
        f"hallucinating model blocked ({d.reason}); money math is deterministic (integer ledger)",
    )


def hostile_prompt_injection() -> ScenarioResult:
    """Injection via support email instructing a refund → untrusted-input guard + refund>cap approval."""
    spec = tools.get("decision_registry.write")
    tool_blocked = spec is not None and tools.blocked_by_input_trust(spec, untrusted_input=True)
    refund_needs_approval = requires_approval(_pay("refund", 150_000, maker="support_agent"))
    contained = bool(tool_blocked) and refund_needs_approval
    return ScenarioResult(
        "hostile_prompt_injection",
        "10/AM-13",
        contained,
        "sensitive tool fails closed on untrusted input; over-cap refund needs maker-checker",
    )


def bad_payment() -> ScenarioResult:
    """Duplicate / over-cap / new payee → idempotency, cap, and payee-allowlist all fire."""
    led = InMemoryLedger()
    t = _pay("p", 50_000, payee="known")
    led.post(t, approved_payees=frozenset({"known"}))
    dup_rejected = led.post(t, approved_payees=frozenset({"known"})) is False
    over_cap = _raises(ApprovalRequired, lambda: validate(_pay("o", 150_000)))
    # New payee derived from the destination account (payee field left None) — cannot be dodged.
    external = Transaction(
        "n", "kn", (Posting("external:attacker_acct", 50_000), Posting("cash", -50_000)), maker="cfo_agent"
    )
    new_payee = _raises(ApprovalRequired, lambda: validate(external, approved_payees=frozenset()))
    contained = dup_rejected and over_cap and new_payee
    return ScenarioResult(
        "bad_payment",
        "AM-11",
        contained,
        "duplicate rejected (idempotency); over-cap + new payee require approval",
    )


def failed_dependency() -> ScenarioResult:
    """Event backbone re-delivers a message → idempotent consumer applies it exactly once."""
    led = InMemoryLedger()
    t = Transaction("d", "kd", (Posting("a", 10_000), Posting("b", -10_000)), maker="cfo_agent")
    led.post(t)
    replay_noop = led.post(t) is False  # at-least-once redelivery
    contained = replay_noop and led.trial_balance() == 0 and led.account_balance("a") == 10_000
    return ScenarioResult(
        "failed_dependency",
        "04",
        contained,
        "redelivered event applied exactly once (idempotent consumer); balance intact",
    )


def stale_forecast() -> ScenarioResult:
    """Forecast confidence/freshness below threshold → KPIs not served (decision blocked)."""
    now = datetime.now(tz=UTC)
    not_built = readiness(Freshness(rows=0, latest_event_at=None, latest_ingested_at=None), now)
    stale = readiness(
        Freshness(rows=5, latest_event_at=now, latest_ingested_at=now - timedelta(hours=1)),
        now,
        sla_seconds=60,
    )
    contained = (not not_built.ready) and (not stale.ready)
    return ScenarioResult(
        "stale_forecast",
        "13/freshness",
        contained,
        "readiness gate blocks serving KPIs when the warehouse is unbuilt or stale",
    )


def dsar_erasure_with_legal_hold() -> ScenarioResult:
    """Erasure request with a financial legal hold → erasure propagates, financial records are
    retained + itemized with their lawful basis (Art.17(3)(b)), and the plan is evidenced."""
    plan = erasure_plan("subject-under-test")
    financial_hold = any(
        (r.get("retentionPolicy") == "financial_retention") or (r.get("lawfulBasis") == "legal_obligation")
        for r in plan.retained_under_hold
    )
    contained = bool(plan.erased) and financial_hold and plan.evidenced
    return ScenarioResult(
        "dsar_erasure_with_legal_hold",
        "09/AM-16",
        contained,
        f"{len(plan.erased)} element(s) erased; {len(plan.retained_under_hold)} retained under legal "
        "hold, itemized with lawful basis (evidenced)",
    )


def incident_rollback() -> ScenarioResult:
    """Sev1 outage during a release that touched PII → auto-rollback to the last good version,
    release freeze (change/error-budget), postmortem required, and a PII breach assessment."""
    release = ReleaseManager(current="v1")
    release.deploy("v2-bad")  # the release that triggers the incident
    budget = ErrorBudget(slo_target=0.99, window=1000)  # 10 errors allowed
    resp = handle_incident(
        Incident("inc-1", Severity.SEV1, touched_pii=True, summary="outage during v2-bad release"),
        release,
        budget,
        errors=250,  # well over budget
    )
    contained = (
        resp.rolled_back
        and release.current == "v1"  # actually reverted to the last good version
        and resp.release_frozen
        and not release.can_release(budget, errors=250)  # further deploys blocked
        and resp.postmortem_required
        and resp.breach_assessment_required
    )
    return ScenarioResult(
        "incident_rollback",
        "03/10",
        contained,
        "Sev1 auto-rolled back to last-good, releases frozen, postmortem + PII breach assessment required",
    )


def losing_business_sunset() -> ScenarioResult:
    """A business racks up conclusive experiment losses → the portfolio allocator sunsets it and
    reclaims its capital (a runaway loser can't keep consuming capital)."""
    from ab_portfolio.core import Action, BusinessPerformance, allocate

    perfs = [BusinessPerformance(business_id="sinker", capital_minor=200_000, kill_count=3)]
    rec = allocate(perfs, portfolio_budget_minor=500_000)[0]
    contained = rec.action is Action.SUNSET and rec.capital_delta == -200_000
    return ScenarioResult(
        "losing_business_sunset",
        "portfolio/ADR-0033",
        contained,
        "a conclusive loser is sunset and its 200k capital reclaimed",
    )


def over_budget_llm_call() -> ScenarioResult:
    """An agent tries a model call that would breach the business's LLM budget → the gateway gate
    refuses it before any inference (runaway inference spend can't happen)."""
    from ab_gateway.llm_budget import LLMBudgetExceeded, gate_llm_spend

    denied = _raises(
        LLMBudgetExceeded,
        lambda: gate_llm_spend("acme", cost_minor=60_000, spent_minor=50_000, budget_minor=100_000),
    )
    return ScenarioResult(
        "over_budget_llm_call",
        "gateway/ADR-0035",
        denied,
        "a call over the per-business LLM budget is refused before inference",
    )


def cross_business_isolation() -> ScenarioResult:
    """Two businesses share the ledger → one's spend/revenue must never leak into the other's
    attribution (multi-tenancy isolation holds under mixed activity)."""
    from ab_revenue.core import Charge, record_charges
    from ab_revenue.gateway import StubRevenueGateway

    led = InMemoryLedger()
    led.post(
        Transaction(
            "la",
            "kla",
            (Posting("a:llm_spend", 30_000), Posting("a:cash", -30_000)),
            maker="gateway",
            business_id="a",
        )
    )
    record_charges(
        StubRevenueGateway(
            [Charge(business_id="b", amount_minor=80_000, customer_ref="c", external_ref="r")]
        ),
        led,
    )
    contained = (
        led.business_spend("a").llm_spend_minor == 30_000
        and led.business_spend("b").llm_spend_minor == 0
        and led.business_revenue("b") == 80_000
        and led.business_revenue("a") == 0
    )
    return ScenarioResult(
        "cross_business_isolation",
        "P1/P4 multi-tenancy",
        contained,
        "business A's LLM spend and business B's revenue stay attributed to their own business_id",
    )


def unprofitable_winner_held() -> ScenarioResult:
    """A business wins its experiments but loses money → the econ→portfolio loop holds its capital
    (capital never chases a money-loser, even a high-scoring one)."""
    from ab_econ.core import UnitInputs, economics, unprofitable_ids
    from ab_portfolio.core import Action, BusinessPerformance, allocate

    losers = unprofitable_ids(
        [
            economics(
                UnitInputs(
                    business_id="hog",
                    revenue_minor=100_000,
                    cogs_minor=100_000,
                    ad_spend_minor=100_000,
                    llm_spend_minor=100_000,
                    customers=10,
                )
            )
        ]
    )
    rec = allocate(
        [BusinessPerformance(business_id="hog", capital_minor=100_000, scale_count=4)],
        portfolio_budget_minor=1_000_000,
        unprofitable_business_ids=losers,
    )[0]
    contained = rec.action is Action.HOLD and "unprofitable" in rec.reason
    return ScenarioResult(
        "unprofitable_winner_held",
        "econ+portfolio/ADR-0040",
        contained,
        "a money-losing experiment winner is held, not funded",
    )


SCENARIOS: tuple[Callable[[], ScenarioResult], ...] = (
    bad_model_output,
    hostile_prompt_injection,
    bad_payment,
    failed_dependency,
    stale_forecast,
    dsar_erasure_with_legal_hold,
    incident_rollback,
    losing_business_sunset,
    over_budget_llm_call,
    cross_business_isolation,
    unprofitable_winner_held,
)


def run_all() -> list[ScenarioResult]:
    return [s() for s in SCENARIOS]
