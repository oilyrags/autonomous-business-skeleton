"""Product Engineering demo (PRD 0008 P5), deterministic + no infra.

    uv run python -m ab_product.product_demo   ·   ./abctl product   ·   make product

Drives a validated initiative through the whole spine: classify → blueprint (LLM-proposed) →
charter (its distinct design language) → deterministic Scaffolder → charter-conformance gate → the
gated SDLC (with the human DPIA + launch gates approved) → deploy into the mesh. The stub model
stands in for GLM-5.2; classification, the scaffold, conformance, the gates, and deploy are the real,
replayable code — the LLM never ships un-replayable code.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_product.blueprint import StubProductModel
from ab_product.charter import BusinessCharter, charter_conformance
from ab_product.classify import classify
from ab_product.deployer import StubDeployer
from ab_product.pipeline import GateResult, Stage, advance, approve_human, start
from ab_product.scaffold import scaffold
from ab_schemas.models import ProductInitiative

INITIATIVE = ProductInitiative(
    initiative_id="init-vtwin",
    title="Verifiable AI Vehicle Twin",
    hypothesis="A verifiable AI health twin lifts marketplace conversion.",
    key_features=["AI health scoring", "verifiable history timeline"],
)


@dataclass(frozen=True)
class ProductDemoSummary:
    classification: str
    conformant: bool
    launched: bool
    deployed_url: str


def _drive_to_launched(initiative_id: str, business_id: str, echo) -> bool:  # type: ignore[no-untyped-def]
    """Advance the gated SDLC to launched, approving the DPIA + launch human gates."""
    state = start(initiative_id, business_id)
    while state.status != "launched":
        if state.status == "awaiting_human":
            echo(f"    [{state.stage.value}] human gate → approved")
            state = approve_human(state, actor="operator")
        else:
            state = advance(state, GateResult(ok=True))
    return state.stage is Stage.LAUNCHED


def run(*, verbose: bool = True) -> ProductDemoSummary:
    echo = print if verbose else (lambda *_a, **_k: None)

    classification = classify(INITIATIVE)
    blueprint = StubProductModel().spec(
        INITIATIVE, classification.business_id
    )  # LLM seam (abstains → default)
    charter = BusinessCharter(
        business_id=classification.business_id, version=1, tokens=blueprint.design_tokens
    )
    plan = scaffold(blueprint, charter)
    report = charter_conformance(plan.artifact, charter)

    echo(f"\n=== Product Engineering — {INITIATIVE.title} ===")
    echo(f"  classification: {classification.kind.upper()} — {classification.rationale}")
    echo(
        f"  design language: primary {charter.tokens.primary} · accent {charter.tokens.accent} "
        "(distinct per business)"
    )
    echo(f"  scaffold: {plan.service_name} ({len(plan.files)} files) · charter-conformant: {report.ok}")

    echo("  gated SDLC:")
    launched = _drive_to_launched(INITIATIVE.initiative_id, classification.business_id, echo)

    deployer = StubDeployer()
    result = deployer.deploy(plan)
    echo(f"  deployed: {result.url}")
    echo(
        "\n  LLM proposed the spec/tokens; classify, scaffold, conformance, gates, deploy are deterministic."
    )

    return ProductDemoSummary(
        classification=classification.kind,
        conformant=report.ok,
        launched=launched,
        deployed_url=result.url,
    )


def main() -> int:
    s = run()
    return 0 if (s.conformant and s.launched and s.deployed_url.startswith("http://")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
