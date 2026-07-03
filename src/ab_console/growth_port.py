"""The growth port: how the console proposes an experiment (PRD 0007 E2).

The console never creates experiments itself — it dispatches through the governed
`growth.experiment.create` gateway tool, so the GUI can do nothing an agent couldn't. The console
authenticated the human operator (VULN-001); it vouches for that identity to the gateway by calling
under a **service credential mapped to `growth.experiment_design_agent`** and recording the operator
as `maker` in the tool metadata — one governed path, dual attribution. The stub records for tests +
the demo; the HTTP adapter targets the real gateway.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from ab_schemas.models import ExperimentCreate

# The service agent identity the console acts as when proposing on an operator's behalf.
SERVICE_AGENT = "growth.experiment_design_agent"


@dataclass(frozen=True)
class GrowthOutcome:
    ok: bool
    experiment_id: str | None
    detail: str


class GrowthPort(Protocol):
    """Create a governed experiment proposal through the gateway."""

    def create(self, proposal: ExperimentCreate, *, maker: str) -> GrowthOutcome: ...


@dataclass
class StubGrowthPort:
    """Records proposals for tests + the demo; no network. Returns a deterministic id."""

    created: list[dict[str, object]] = field(default_factory=list)

    def create(self, proposal: ExperimentCreate, *, maker: str) -> GrowthOutcome:
        self.created.append(
            {
                "business_id": proposal.business_id,
                "hypothesis": proposal.hypothesis,
                "arm_names": [a.name for a in proposal.arms],
                "budget_minor": proposal.budget_minor,
                "success_metrics": proposal.success_metrics,
                "maker": maker,
            }
        )
        experiment_id = f"exp_stub_{len(self.created)}"
        return GrowthOutcome(ok=True, experiment_id=experiment_id, detail=f"created {experiment_id}")


class HttpGrowthPort:
    """Call `growth.experiment.create` on the real gateway, under the service agent identity, with
    the operator recorded in metadata (governed + audited). `token_provider` mints the agent's OIDC
    token (the console holds the service credential)."""

    def __init__(self, token_provider: Callable[[], str], base_url: str = "http://localhost:18090") -> None:
        self._token = token_provider
        self._base_url = base_url.rstrip("/")

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
