"""The experiment-proposer seam (PRD 0007): dispatch a proposal through the governed
`growth.experiment.create` path. One contract, consumed by both the ideation engine
(`propose_ideas`) and the console workspace — so the growth context owns it and there is no
duplicate port/stub across the layer boundary (code-review #3).

The growth context still never imports the gateway/console: the real adapter (the console's
`HttpGrowthPort`, a gateway client) implements this Protocol; the stub records for tests + demos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ab_schemas.models import ExperimentCreate


@dataclass(frozen=True)
class GrowthOutcome:
    ok: bool
    experiment_id: str | None
    detail: str


class ExperimentProposer(Protocol):
    """Create a governed experiment proposal; returns the outcome (id on success)."""

    def create(self, proposal: ExperimentCreate, *, maker: str) -> GrowthOutcome: ...


@dataclass
class StubExperimentProposer:
    """Records proposals for tests + demos; returns a deterministic id. Same contract the real
    gateway-backed adapter implements."""

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
