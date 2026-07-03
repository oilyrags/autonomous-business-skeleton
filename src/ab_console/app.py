"""The console FastAPI app: renders the deterministic view-models through the HIG design system.

In production the providers read live state (ledger → ab_obs, monitor checks, kill switch, growth
outcomes, the decisions table); here they return deterministic samples so every page renders with
no infra. Each provider is a FastAPI dependency, so tests override them (empty states, kill-switch
banner, filters). Mutations (the kill switch) go through the governed port — the console can do
nothing an agent couldn't.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ab_console.approvals import ApprovalPort, StubApprovalPort
from ab_console.auth import Operator, check_origin, require_mutator, require_operator
from ab_console.growth_port import GrowthPort, StubGrowthPort
from ab_console.killswitch_port import KillSwitchPort, StubKillSwitchPort
from ab_console.stream import SAMPLE_EVENTS, sse_format
from ab_console.viewmodels import (
    CONFIRM_PHRASE,
    AuditRow,
    ExperimentRow,
    FleetView,
    PendingDecision,
    action_badge,
    audit_view,
    build_proposal,
    business_detail,
    decisions_view,
    experiments_view,
    fleet,
    fmt_money,
    intervention_view,
    sparkline_points,
    status_badge,
)
from ab_econ.core import UnitEconomics, UnitInputs, economics
from ab_monitor.check import CheckResult, CheckStatus, cert_expiry_check, slo_burn_check
from ab_monitor.prometheus import CONTENT_TYPE as PROMETHEUS_CONTENT_TYPE
from ab_monitor.prometheus import exposition
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot
from ab_ops.reliability import ErrorBudget

_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(_DIR / "templates"))
templates.env.filters["money"] = fmt_money
templates.env.filters["spark"] = sparkline_points
templates.env.filters["status_badge"] = status_badge
templates.env.filters["action_badge"] = action_badge

app = FastAPI(title="ab_console")
app.mount("/static", StaticFiles(directory=str(_DIR / "static")), name="static")


@dataclass(frozen=True)
class Chrome:
    """Top-bar + nav state shared by every page."""

    nav: str
    kill_switch_active: bool
    alert_count: int


# --- Sample data (a live deployment replaces these providers with real reads) --------------------

_SAMPLE_SNAPSHOTS = [
    BusinessSnapshot("rocket", 1_000_000, 20_000, 50_000, 880_000, 500, "profitable"),
    BusinessSnapshot("steady", 400_000, 15_000, 30_000, 120_000, 375, "profitable"),
    BusinessSnapshot("hog", 250_000, 200_000, 0, -30_000, 8_000, "unprofitable"),
]
_SAMPLE_CHECKS = [
    CheckResult("hog-health", CheckStatus.CRITICAL, "operating loss", business_id="hog"),
    CheckResult("rocket-health", CheckStatus.OK, "rocket healthy (profitable)", business_id="rocket"),
    slo_burn_check("gateway", ErrorBudget(slo_target=0.99, window=1000), errors=7),  # 70% burned
    cert_expiry_check("gateway", days_remaining=45, warn_days=30, crit_days=14),
]
_SAMPLE_ANOMALIES = [Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating profit -30000 < floor")]
_SAMPLE_ECON: dict[str, UnitEconomics] = {
    s.business_id: economics(
        UnitInputs(
            business_id=s.business_id,
            revenue_minor=s.revenue_minor,
            cogs_minor=100_000,
            ad_spend_minor=s.ad_spend_minor,
            llm_spend_minor=s.llm_spend_minor,
            customers=100,
        ),
        expected_lifetime_periods=12,
    )
    for s in _SAMPLE_SNAPSHOTS
}
_SAMPLE_EXPERIMENTS = [
    ExperimentRow(
        "exp-cta-1",
        "rocket",
        "question CTA lifts engagement",
        "scale",
        "significant win",
        0.0001,
        0.08,
        0.04,
        0.12,
    ),
    ExperimentRow(
        "exp-price-2",
        "hog",
        "lower price lifts conversion",
        "kill",
        "CAC over ceiling",
        0.2000,
        0.01,
        0.03,
        0.04,
    ),
]
_SAMPLE_AUDIT = [
    AuditRow("dec-001", "executive.cmo_agent", 2, "autonomous_within_policy", "rocket", "2026-07-02 09:14"),
    AuditRow("dec-002", "treasury.control_agent", 4, "approved", "hog", "2026-07-02 09:20"),
    AuditRow("dec-003", "growth.experiment_agent", 1, "autonomous_within_policy", None, "2026-07-02 10:02"),
]

_SAMPLE_HISTORY = {  # recent operating-profit series (oldest first) for the sparklines
    "rocket": (520_000, 610_000, 590_000, 700_000, 810_000, 880_000),
    "steady": (90_000, 100_000, 110_000, 105_000, 118_000, 120_000),
    "hog": (40_000, 25_000, 10_000, -5_000, -18_000, -30_000),
}
_SAMPLE_PENDING = [
    PendingDecision(
        "pend-201",
        "payment",
        "Pay supplier invoice over the cap",
        150_000,
        "executive.cmo_agent",
        4,
        "rocket",
    ),
    PendingDecision(
        "pend-202",
        "reallocation",
        "Sunset 'sinker' and reclaim its capital",
        200_000,
        "executive.portfolio_agent",
        5,
        "sinker",
    ),
]

_STUB_KILLSWITCH = StubKillSwitchPort()
_STUB_APPROVALS = StubApprovalPort()
_STUB_GROWTH = StubGrowthPort()


def fleet_provider() -> FleetView:
    return fleet(
        _SAMPLE_SNAPSHOTS,
        anomalies=_SAMPLE_ANOMALIES,
        checks=_SAMPLE_CHECKS,
        kill_switch_active=False,
        history=_SAMPLE_HISTORY,
    )


def snapshots_provider() -> list[BusinessSnapshot]:
    return _SAMPLE_SNAPSHOTS


def econ_provider() -> dict[str, UnitEconomics]:
    return _SAMPLE_ECON


def checks_provider() -> list[CheckResult]:
    return _SAMPLE_CHECKS


def experiments_provider() -> list[ExperimentRow]:
    return _SAMPLE_EXPERIMENTS


def audit_provider() -> list[AuditRow]:
    return _SAMPLE_AUDIT


def audit_integrity_provider() -> bool:
    return True


def kill_switch_state_provider() -> tuple[bool, str | None]:
    """(active, reason) — a live deployment reads the kill-switch table."""
    return (False, None)


def killswitch_port_provider() -> KillSwitchPort:
    """The governed activation path. A live deployment returns HttpKillSwitchPort()."""
    return _STUB_KILLSWITCH


def _chrome(nav: str, view_or_state: FleetView | tuple[bool, str | None], alert_count: int) -> Chrome:
    active = view_or_state.kill_switch_active if isinstance(view_or_state, FleetView) else view_or_state[0]
    return Chrome(nav=nav, kill_switch_active=active, alert_count=alert_count)


# --- Routes ----------------------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def fleet_dashboard(
    request: Request,
    view: Annotated[FleetView, Depends(fleet_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    chrome = _chrome("fleet", view, view.alert_count)
    return templates.TemplateResponse(request, "fleet.html", {"view": view, "chrome": chrome})


@app.get("/business/{business_id}", response_class=HTMLResponse)
def business_page(
    request: Request,
    business_id: str,
    snapshots: Annotated[list[BusinessSnapshot], Depends(snapshots_provider)],
    econ: Annotated[dict[str, UnitEconomics], Depends(econ_provider)],
    checks: Annotated[list[CheckResult], Depends(checks_provider)],
    experiments: Annotated[list[ExperimentRow], Depends(experiments_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    view = business_detail(business_id, snapshots, econ, checks, experiments)
    chrome = _chrome("fleet", ks, 0)
    if view is None:
        return templates.TemplateResponse(
            request, "notfound.html", {"business_id": business_id, "chrome": chrome}, status_code=404
        )
    return templates.TemplateResponse(request, "business.html", {"view": view, "chrome": chrome})


def growth_port_provider() -> GrowthPort:
    """The governed propose path. A live deploy returns HttpGrowthPort(token_provider=…)."""
    return _STUB_GROWTH


@app.get("/experiments", response_class=HTMLResponse)
def experiments_page(
    request: Request,
    rows: Annotated[list[ExperimentRow], Depends(experiments_provider)],
    snapshots: Annotated[list[BusinessSnapshot], Depends(snapshots_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
    business_id: str | None = None,
) -> HTMLResponse:
    view = experiments_view(rows, business_id=business_id)
    chrome = _chrome("experiments", ks, 0)
    return templates.TemplateResponse(
        request,
        "experiments.html",
        {"view": view, "chrome": chrome, "businesses": [s.business_id for s in snapshots]},
    )


@app.post("/experiments/propose", response_class=HTMLResponse)
async def experiments_propose(
    request: Request,
    rows: Annotated[list[ExperimentRow], Depends(experiments_provider)],
    snapshots: Annotated[list[BusinessSnapshot], Depends(snapshots_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    operator: Annotated[Operator, Depends(require_operator)],
    port: Annotated[GrowthPort, Depends(growth_port_provider)],
) -> HTMLResponse:
    """Propose an experiment through the governed GrowthPort — the console does nothing an agent
    couldn't; the real operator is recorded as maker (VULN-001 + PRD 0007 E2)."""
    require_mutator(operator)  # proposing spends against a business's runway cap — a mutating action
    check_origin(request)  # CSRF defense in depth
    raw = (await request.body()).decode("utf-8", errors="replace")
    form = {k: v[0] for k, v in parse_qs(raw).items()}
    chrome = _chrome("experiments", ks, 0)

    def _render(
        *, created: str | None = None, error: str | None = None, status_code: int = 200
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "experiments.html",
            {
                "view": experiments_view(rows),
                "chrome": chrome,
                "businesses": [s.business_id for s in snapshots],
                "created": created,
                "propose_error": error,
            },
            status_code=status_code,
        )

    try:
        budget_minor = round(float(form.get("budget", "")) * 100)
    except ValueError:
        return _render(error="Budget must be a number (e.g. 500).", status_code=400)
    try:
        proposal = build_proposal(
            business_id=form.get("business_id", ""),
            hypothesis=form.get("hypothesis", ""),
            control_desc=form.get("control_desc", ""),
            treatment_desc=form.get("treatment_desc", ""),
            budget_minor=budget_minor,
            success_metrics=[m.strip() for m in form.get("success_metrics", "").split(",")],
        )
    except ValueError as exc:
        return _render(error=str(exc), status_code=400)

    outcome = port.create(proposal, maker=operator.id)
    if not outcome.ok:
        return _render(error=f"Proposal failed: {outcome.detail}", status_code=502)
    return _render(created=outcome.experiment_id)


@app.get("/audit", response_class=HTMLResponse)
def audit_page(
    request: Request,
    rows: Annotated[list[AuditRow], Depends(audit_provider)],
    intact: Annotated[bool, Depends(audit_integrity_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
    business_id: str | None = None,
    agent_id: str | None = None,
) -> HTMLResponse:
    # Empty query params arrive as "" — treat them as no filter.
    view = audit_view(
        rows, business_id=business_id or None, agent_id=agent_id or None, integrity_intact=intact
    )
    chrome = _chrome("audit", ks, 0)
    return templates.TemplateResponse(request, "audit.html", {"view": view, "chrome": chrome})


@app.get("/killswitch", response_class=HTMLResponse)
def killswitch_page(
    request: Request,
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    view = intervention_view(kill_switch_active=ks[0], current_reason=ks[1])
    chrome = _chrome("killswitch", ks, 0)
    return templates.TemplateResponse(request, "killswitch.html", {"view": view, "chrome": chrome})


@app.post("/killswitch", response_class=HTMLResponse)
async def killswitch_activate(
    request: Request,
    port: Annotated[KillSwitchPort, Depends(killswitch_port_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    operator: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    """The deliberate action: a required reason + the typed confirm phrase, then the governed port."""
    require_mutator(operator)  # halting the fleet needs a mutating role (least privilege)
    check_origin(request)  # CSRF defense in depth
    # Parse the urlencoded body with the stdlib (no python-multipart dependency needed).
    raw = (await request.body()).decode("utf-8", errors="replace")
    form = {k: v[0] for k, v in parse_qs(raw).items()}
    scope = form.get("scope", "global")
    target_id = form.get("target_id", "")
    reason = form.get("reason", "")
    confirm = form.get("confirm", "")
    chrome = _chrome("killswitch", ks, 0)

    def _render(view: object, status_code: int = 200) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "killswitch.html", {"view": view, "chrome": chrome}, status_code=status_code
        )

    if not reason.strip():
        return _render(
            intervention_view(kill_switch_active=ks[0], error="A reason is required — it is audited."),
            status_code=400,
        )
    if confirm.strip() != CONFIRM_PHRASE:
        return _render(
            intervention_view(
                kill_switch_active=ks[0], error=f"Type {CONFIRM_PHRASE} to confirm — this halts agents."
            ),
            status_code=400,
        )
    result = port.activate(
        scope=scope,
        target_id=target_id.strip() or None,
        reason=reason.strip(),
        activated_by=operator.id,  # the real, signature-verified operator — not a constant
    )
    if not result.ok:
        return _render(
            intervention_view(kill_switch_active=ks[0], error=f"Activation failed: {result.detail}"),
            status_code=502,
        )
    return _render(intervention_view(kill_switch_active=True, activated=True))


# --- v0.2: live feed + decision workspace ----------------------------------------------------------


def decision_events_provider() -> list[dict[str, object]]:
    """The event stream's source. Stub replays samples (and ends); live = a bus consumer."""
    return SAMPLE_EVENTS


def pending_decisions_provider() -> list[PendingDecision]:
    return _SAMPLE_PENDING


def approval_port_provider() -> ApprovalPort:
    """The governed approve/reject path. A gateway-backed adapter replaces this in a live deploy."""
    return _STUB_APPROVALS


@app.get("/events/stream")
def events_stream(
    events: Annotated[list[dict[str, object]], Depends(decision_events_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> StreamingResponse:
    """Server-Sent Events for the live feed — consumed by the browser's native EventSource."""
    return StreamingResponse(sse_format(events), media_type="text/event-stream")


@app.get("/feed", response_class=HTMLResponse)
def feed_page(
    request: Request,
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    chrome = _chrome("feed", ks, 0)
    return templates.TemplateResponse(request, "feed.html", {"chrome": chrome})


@app.get("/decisions", response_class=HTMLResponse)
def decisions_page(
    request: Request,
    pending: Annotated[list[PendingDecision], Depends(pending_decisions_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    _op: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    chrome = _chrome("decisions", ks, 0)
    return templates.TemplateResponse(
        request, "decisions.html", {"view": decisions_view(pending), "chrome": chrome}
    )


@app.post("/decisions/act", response_class=HTMLResponse)
async def decisions_act(
    request: Request,
    pending: Annotated[list[PendingDecision], Depends(pending_decisions_provider)],
    port: Annotated[ApprovalPort, Depends(approval_port_provider)],
    ks: Annotated[tuple[bool, str | None], Depends(kill_switch_state_provider)],
    operator: Annotated[Operator, Depends(require_operator)],
) -> HTMLResponse:
    """Approve or reject a pending decision through the governed port. A rejection needs a note."""
    require_mutator(operator)  # approving a high-stakes decision needs a mutating role
    check_origin(request)  # CSRF defense in depth
    raw = (await request.body()).decode("utf-8", errors="replace")
    form = {k: v[0] for k, v in parse_qs(raw).items()}
    decision_id = form.get("decision_id", "")
    action = form.get("action", "")
    note = form.get("note", "").strip()
    chrome = _chrome("decisions", ks, 0)

    def _render(view: object, status_code: int = 200) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "decisions.html", {"view": view, "chrome": chrome}, status_code=status_code
        )

    known = {d.decision_id for d in pending}
    if decision_id not in known or action not in ("approve", "reject"):
        return _render(decisions_view(pending, error="Unknown decision or action."), status_code=400)
    if action == "reject" and not note:
        return _render(
            decisions_view(pending, error="A note is required to reject — it is audited."),
            status_code=400,
        )
    actor = operator.id  # the real, signature-verified operator — the audit attributes the human
    outcome = (
        port.approve(decision_id, actor=actor, note=note)
        if action == "approve"
        else port.reject(decision_id, actor=actor, note=note)
    )
    if not outcome.ok:
        return _render(decisions_view(pending, error=outcome.detail), status_code=502)
    remaining = [d for d in pending if d.decision_id != decision_id]
    return _render(decisions_view(remaining, acted=outcome.detail))


@app.get("/metrics")
def metrics(
    checks: Annotated[list[CheckResult], Depends(checks_provider)],
    snapshots: Annotated[list[BusinessSnapshot], Depends(snapshots_provider)],
) -> Response:
    """Prometheus scrape target: the same checks + business reads, as gauges (M5). One definition
    per signal — Nagios and Prometheus both consume the deterministic ab_monitor/ab_obs sources.

    Intentionally NOT behind the operator auth (VULN-001): Prometheus scrapes it machine-to-machine
    and cannot present a signed operator identity. It exposes only aggregate business gauges (no
    audit/PII); restrict it at the network layer (scrape it over the internal network / mesh only,
    as the monitoring compose profile does), or front it with a scrape credential in the proxy."""
    return Response(content=exposition(checks, snapshots), media_type=PROMETHEUS_CONTENT_TYPE)
