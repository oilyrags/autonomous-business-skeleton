"""The Deployer (PRD 0008 P4): ship a scaffolded product into the governed mesh, business_id-scoped.

A `Deployer` port keeps the target injectable — `StubDeployer` records for CI (the render-smoke in
`__main__` proves the generated service actually starts + serves its themed page); a real adapter
writes the plan under a `ventures` compose profile and brings it up (k8s/cloud later, same port).
`deploy_product` publishes `ProductDeployed` on success.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ab_common import bus
from ab_common.config import settings
from ab_product.scaffold import ScaffoldPlan
from ab_schemas.events import ProductDeployed, build


@dataclass(frozen=True)
class DeployResult:
    ok: bool
    url: str
    detail: str


class Deployer(Protocol):
    """Deploy a scaffolded product; returns where it is reachable."""

    def deploy(self, plan: ScaffoldPlan) -> DeployResult: ...


def write_plan(plan: ScaffoldPlan, root: Path) -> Path:
    """Write a ScaffoldPlan's files under ``root`` (the ScaffoldWriter real behaviour). Returns the
    written service directory. Deterministic; used by the real deployer + the render-smoke."""
    for file in plan.files:
        target = root / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file.content)
    return root / plan.service_name


@dataclass
class StubDeployer:
    """Records deployments; no network. A real adapter builds + runs the compose ventures service."""

    deployed: list[dict[str, str]] = field(default_factory=list)

    def deploy(self, plan: ScaffoldPlan) -> DeployResult:
        url = f"http://{plan.service_name}.ventures.local"
        self.deployed.append({"business_id": plan.business_id, "service_name": plan.service_name, "url": url})
        return DeployResult(ok=True, url=url, detail=f"deployed {plan.service_name}")


def deploy_product(
    plan: ScaffoldPlan, *, initiative_id: str, product_id: str, deployer: Deployer
) -> DeployResult:
    """Deploy through the injected Deployer and, on success, publish `ProductDeployed`."""
    result = deployer.deploy(plan)
    if result.ok:
        event = build(
            ProductDeployed,
            subject=("Product", product_id),
            producer="product.engineering_agent",
            business_id=plan.business_id,
            initiative_id=initiative_id,
            product_id=product_id,
            service_name=plan.service_name,
            url=result.url,
        )
        bus.publish_event(settings.product_deployed_topic, key=product_id, event=event)
    return result
