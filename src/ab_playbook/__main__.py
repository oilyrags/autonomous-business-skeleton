"""Living Playbooks demo (deterministic, no infra).

    uv run python -m ab_playbook

Distil the blueprints of three winning businesses into a versioned playbook (median economics +
majority modules, aggregate-only), then instantiate a brand-new business from it.
"""

from __future__ import annotations

from ab_growth.blueprint import Blueprint
from ab_playbook.core import apply_playbook, extract_playbook

WINNERS = [
    Blueprint(
        business_id="a",
        name="A",
        target_revenue_minor=1_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=3_000,
        enabled_modules=("waitlist", "checkout"),
    ),
    Blueprint(
        business_id="b",
        name="B",
        target_revenue_minor=1_200_000,
        experiment_budget_minor=250_000,
        min_conversion_rate=0.06,
        max_cac_minor=5_000,
        enabled_modules=("waitlist", "referral"),
    ),
    Blueprint(
        business_id="c",
        name="C",
        target_revenue_minor=800_000,
        experiment_budget_minor=150_000,
        min_conversion_rate=0.05,
        max_cac_minor=4_000,
        enabled_modules=("waitlist", "checkout"),
    ),
]


def main() -> int:
    pb = extract_playbook(WINNERS, version="v1")
    print(f"  playbook {pb.version} from {pb.sample_size} winners:")
    print(f"    median max_cac={pb.max_cac_minor}  min_conversion_rate={pb.min_conversion_rate}")
    print(f"    recommended modules: {pb.recommended_modules}  (freq {pb.module_frequency})")
    bp = apply_playbook(pb, business_id="newco", name="NewCo")
    print(f"\n  instantiated 'newco' -> cac={bp.max_cac_minor} modules={bp.enabled_modules}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
