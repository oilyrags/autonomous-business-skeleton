"""The skeleton-native Deployer (PRD 0008 P4): a scaffolded product ships as a FastAPI + vendored-
daisyUI service into the governed compose mesh, business_id-scoped, behind a Deployer port. Infra-free."""

from __future__ import annotations

import yaml

from ab_product.blueprint import StubProductModel
from ab_product.charter import BusinessCharter
from ab_product.scaffold import scaffold
from ab_schemas.models import ProductInitiative


def _plan(business_id: str = "vehicle-twin") -> object:
    init = ProductInitiative(initiative_id="i1", title="Vehicle Twin", key_features=["x"])
    blueprint = StubProductModel().spec(init, business_id)
    charter = BusinessCharter(business_id=business_id, version=1, tokens=blueprint.design_tokens)
    return scaffold(blueprint, charter)


def test_scaffold_emits_a_dockerfile_and_a_valid_compose_fragment() -> None:
    plan = _plan()
    paths = {f.path for f in plan.files}  # type: ignore[attr-defined]
    assert any(p.endswith("Dockerfile") for p in paths)

    fragment = next(f for f in plan.files if f.path.endswith("compose.fragment.yml"))  # type: ignore[attr-defined]
    parsed = yaml.safe_load(fragment.content)  # valid YAML
    (service,) = parsed["services"].values()
    assert service["build"].endswith(plan.service_name)  # type: ignore[attr-defined]
    assert any("business_id=vehicle-twin" in label for label in service["labels"])  # tenant-labelled


def test_deploy_records_and_publishes_product_deployed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_product.deployer import StubDeployer, deploy_product

    published: list[str] = []
    monkeypatch.setattr("ab_product.deployer.bus.publish", lambda topic, *, key, value: published.append(key))
    plan = _plan()
    deployer = StubDeployer()
    result = deploy_product(plan, initiative_id="i1", product_id="prod_vehicle-twin", deployer=deployer)

    assert result.ok and result.url.startswith("http://")
    assert deployer.deployed[0]["service_name"] == plan.service_name  # type: ignore[attr-defined]
    assert published == ["prod_vehicle-twin"]  # ProductDeployed emitted once


def test_the_scaffolded_service_starts_and_serves_its_themed_page(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # The render-smoke (like `make console`): write the plan, import the GENERATED FastAPI app, serve.
    import importlib.util

    from fastapi.testclient import TestClient

    from ab_product.deployer import write_plan

    plan = _plan()
    service_dir = write_plan(plan, tmp_path)  # type: ignore[arg-type]
    spec = importlib.util.spec_from_file_location("venture_app", service_dir / "app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    resp = TestClient(module.app).get("/")
    assert resp.status_code == 200
    assert 'data-theme="vehicle-twin"' in resp.text  # the generated service serves its themed page
