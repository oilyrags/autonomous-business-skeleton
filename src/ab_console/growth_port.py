"""The console's real experiment proposer (PRD 0007 E2): dispatch a proposal to the governed
`growth.experiment.create` gateway tool.

The console never creates experiments itself — the GUI can do nothing an agent couldn't. Having
authenticated the human operator (VULN-001), it vouches for that identity to the gateway by calling
under a **service credential mapped to `growth.experiment_design_agent`** and recording the operator
as `maker` in the tool metadata — one governed path, dual attribution. This `HttpGrowthPort`
implements the shared `ab_growth.proposer.ExperimentProposer` seam (the stub lives there too, #3).
"""

from __future__ import annotations

import os
from collections.abc import Callable

from ab_growth.proposer import GrowthOutcome
from ab_schemas.models import ExperimentCreate

# The service agent identity the console acts as when proposing on an operator's behalf.
SERVICE_AGENT = "growth.experiment_design_agent"


class HttpGrowthPort:
    """Call `growth.experiment.create` on the real gateway, under the service agent identity, with
    the operator recorded in metadata (governed + audited). Implements `ExperimentProposer`.
    `token_provider` mints the agent's OIDC token (the console holds the service credential). The
    gateway ingress is `AB_GATEWAY_URL` (the governed `/tool-call` endpoint)."""

    def __init__(self, token_provider: Callable[[], str], base_url: str | None = None) -> None:
        self._token = token_provider
        self._base_url = (base_url or os.environ.get("AB_GATEWAY_URL", "http://localhost:18080")).rstrip("/")

    def create(self, proposal: ExperimentCreate, *, maker: str) -> GrowthOutcome:
        import httpx  # lazy: only for a real proposal

        args = proposal.model_dump()
        args["metadata"] = {**args.get("metadata", {}), "operator": maker}  # dual attribution
        resp = httpx.post(
            f"{self._base_url}/tool-call",
            headers={"Authorization": f"Bearer {self._token()}"},
            json={"tool": "growth.experiment.create", "purpose": f"operator {maker} proposal", "args": args},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return GrowthOutcome(ok=False, experiment_id=None, detail=resp.text)
        experiment_id = resp.json().get("decision_id")
        return GrowthOutcome(ok=True, experiment_id=experiment_id, detail=f"created {experiment_id}")
