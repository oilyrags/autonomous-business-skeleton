"""MVP generator + deployer demo (deterministic, no infra).

    uv run python -m ab_mvp

A Blueprint is turned into a landing page and 'deployed' via the stub deployer, returning a URL an
experiment can point traffic at. A real Vercel/Netlify/container adapter slots in behind the port.
"""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_mvp.core import deploy_mvp
from ab_mvp.deployer import StubDeployer

BLUEPRINTS = [
    Blueprint(
        business_id="rocket",
        name="Rocket",
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.05,
        max_cac_minor=4_000,
        enabled_modules=("waitlist", "checkout"),
    ),
    Blueprint(
        business_id="steady",
        name="Steady",
        target_revenue_minor=500_000,
        experiment_budget_minor=100_000,
        min_conversion_rate=0.03,
        max_cac_minor=6_000,
        enabled_modules=("waitlist",),
    ),
]


def main() -> int:
    deployer = StubDeployer()
    for bp in BLUEPRINTS:
        deployment, event = deploy_mvp(bp, deployer)
        print(f"  {bp.business_id:7} deployed -> {deployment.url}  (page {deployment.content_hash[:12]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
