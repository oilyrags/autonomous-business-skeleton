"""Failure-injection scenarios from architecture/16. Each returns a ScenarioResult; the
suite passes if every non-deferred scenario is CONTAINED. Deterministic, no infra: it drives
the real control code (eval gate, tool registry, ledger, freshness) with injected failures.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ab_data.freshness import Freshness, readiness
from ab_evals.gate import evaluate_and_gate
from ab_evals.models import HallucinatingModel
from ab_evals.suites import SIGNIFICANT_CUSTOMER_DECISION
from ab_gateway import tools
from ab_ledger.core import ApprovalRequired, InMemoryLedger, Posting, Transaction, requires_approval, validate


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
    new_payee = _raises(
        ApprovalRequired,
        lambda: validate(_pay("n", 50_000, payee="attacker_acct"), approved_payees=frozenset()),
    )
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
    return ScenarioResult(
        "dsar_erasure_with_legal_hold",
        "09/AM-16",
        False,
        "no DSAR erasure/legal-hold flow implemented yet (Compliance phase)",
        deferred=True,
    )


def incident_rollback() -> ScenarioResult:
    return ScenarioResult(
        "incident_rollback",
        "03/10",
        False,
        "no deploy/rollback/error-budget component implemented yet (SRE phase)",
        deferred=True,
    )


SCENARIOS: tuple[Callable[[], ScenarioResult], ...] = (
    bad_model_output,
    hostile_prompt_injection,
    bad_payment,
    failed_dependency,
    stale_forecast,
    dsar_erasure_with_legal_hold,
    incident_rollback,
)


def run_all() -> list[ScenarioResult]:
    return [s() for s in SCENARIOS]
