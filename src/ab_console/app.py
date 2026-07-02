"""The console FastAPI app: renders the deterministic view-models through the HIG design system.

In production the fleet provider reads live snapshots (ledger → ab_obs) + monitor checks + the
kill-switch state; here it returns a deterministic sample so the page renders with no infra. The
provider is a FastAPI dependency, so tests can override it (e.g. to exercise the empty state).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ab_console.viewmodels import FleetView, fleet, fmt_money
from ab_monitor.check import CheckResult, CheckStatus
from ab_obs.core import Anomaly, AnomalyKind, BusinessSnapshot

_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(_DIR / "templates"))
templates.env.filters["money"] = fmt_money

app = FastAPI(title="ab_console")
app.mount("/static", StaticFiles(directory=str(_DIR / "static")), name="static")

_SAMPLE_SNAPSHOTS = [
    BusinessSnapshot("rocket", 1_000_000, 20_000, 50_000, 880_000, 500, "profitable"),
    BusinessSnapshot("steady", 400_000, 15_000, 30_000, 120_000, 375, "profitable"),
    BusinessSnapshot("hog", 250_000, 200_000, 0, -30_000, 8_000, "unprofitable"),
]
_SAMPLE_CHECKS = [
    CheckResult("hog-health", CheckStatus.CRITICAL, "operating loss", business_id="hog"),
]
_SAMPLE_ANOMALIES = [Anomaly("hog", AnomalyKind.OPERATING_LOSS, "operating profit -30000 < floor")]


def fleet_provider() -> FleetView:
    """The live fleet view. Overridden in tests; sample data here so the page renders infra-free."""
    return fleet(
        _SAMPLE_SNAPSHOTS,
        anomalies=_SAMPLE_ANOMALIES,
        checks=_SAMPLE_CHECKS,
        kill_switch_active=False,
    )


@app.get("/", response_class=HTMLResponse)
def fleet_dashboard(request: Request, view: Annotated[FleetView, Depends(fleet_provider)]) -> HTMLResponse:
    return templates.TemplateResponse(request, "fleet.html", {"view": view})
