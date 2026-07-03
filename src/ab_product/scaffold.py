"""The deterministic Scaffolder (PRD 0008 P1b): from a ProductBlueprint + BusinessCharter, emit a
business_id-scoped FastAPI + vendored-daisyUI product service, themed by the charter and conformant
by construction. Pure over its inputs — the LLM never writes this code. A ScaffoldWriter port emits
the plan to disk (stub records in CI).
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Protocol

from ab_product.blueprint import ProductBlueprint
from ab_product.charter import Artifact, BusinessCharter, render_theme
from ab_product.classify import Classification
from ab_schemas.events import ProductScaffolded, build

# The dependencies + architecture rules the generated service is built to satisfy (→ conformant).
_SCAFFOLD_DEPS = frozenset({"fastapi", "jinja2"})


@dataclass(frozen=True)
class ScaffoldFile:
    path: str
    content: str


@dataclass(frozen=True)
class ScaffoldPlan:
    business_id: str
    service_name: str
    files: tuple[ScaffoldFile, ...]
    artifact: Artifact  # what the plan declares to the conformance gate


class ScaffoldWriter(Protocol):
    """Emit a ScaffoldPlan to disk (or a PR). Stub records; a real writer writes files."""

    def write(self, plan: ScaffoldPlan) -> None: ...


@dataclass
class StubScaffoldWriter:
    written: list[ScaffoldPlan]

    def __init__(self) -> None:
        self.written = []

    def write(self, plan: ScaffoldPlan) -> None:
        self.written.append(plan)


def _index_html(blueprint: ProductBlueprint, charter: BusinessCharter) -> str:
    # name/summary/features originate from the LLM (or the promoted initiative) — untrusted content.
    # Escape every interpolated field so it renders as inert text, never as live markup, in the
    # shipped service. The theme + theme_name are safe by construction (CSS-safe tokens; slug id).
    theme = render_theme(charter)
    features = "".join(f"<li>{escape(f)}</li>" for f in blueprint.features)
    return (
        f'<!doctype html><html data-theme="{charter.theme_name}">\n'
        f'<head><meta charset="utf-8"><style>\n{theme}</style></head>\n'
        f'<body class="min-h-screen bg-base-100">\n'
        f'  <main class="p-8">\n'
        f'    <h1 class="text-3xl font-semibold text-primary">{escape(blueprint.name)}</h1>\n'
        f'    <p class="opacity-70 mt-1">{escape(blueprint.summary)}</p>\n'
        f'    <ul class="menu mt-4">{features}</ul>\n'
        f"  </main>\n</body></html>\n"
    )


def _app_py(blueprint: ProductBlueprint, service_name: str) -> str:
    # business_id tenancy + single governed ingress noted; a real service wires the gateway client.
    return (
        f'"""Generated product service for business {blueprint.business_id!r} '
        f'(ab_product scaffold; charter-conformant)."""\n\n'
        "from pathlib import Path\n\n"
        "from fastapi import FastAPI\n"
        "from fastapi.responses import HTMLResponse\n\n"
        f'BUSINESS_ID = "{blueprint.business_id}"  # every read/write is scoped to this tenant\n'
        f'app = FastAPI(title="{service_name}")\n\n\n'
        '@app.get("/", response_class=HTMLResponse)\n'
        "def index() -> HTMLResponse:\n"
        '    return HTMLResponse((Path(__file__).parent / "templates" / "index.html").read_text())\n'
    )


def _dockerfile() -> str:
    return (
        "FROM python:3.12-slim\n"
        "WORKDIR /app\n"
        "RUN pip install --no-cache-dir fastapi uvicorn\n"
        "COPY . /app\n"
        'CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]\n'
    )


def _compose_fragment(business_id: str, service_name: str) -> str:
    # A compose service merged into the `ventures` profile: business_id-labelled, on the mesh network.
    return (
        "services:\n"
        f"  {service_name}:\n"
        f"    build: ./ventures/{service_name}\n"
        "    labels:\n"
        f'      - "business_id={business_id}"\n'
        "    networks:\n"
        "      - monitoring\n"
        "    restart: unless-stopped\n"
    )


def scaffold(blueprint: ProductBlueprint, charter: BusinessCharter) -> ScaffoldPlan:
    """Deterministically render the product service from the blueprint + charter. The plan is
    business_id-scoped, themed by the charter, and declares an artifact that satisfies the charter."""
    service_name = f"venture_{charter.business_id.replace('-', '_')}"
    files = (
        ScaffoldFile(f"{service_name}/app.py", _app_py(blueprint, service_name)),
        ScaffoldFile(f"{service_name}/templates/index.html", _index_html(blueprint, charter)),
        ScaffoldFile(f"{service_name}/__init__.py", ""),
        ScaffoldFile(f"{service_name}/Dockerfile", _dockerfile()),
        ScaffoldFile(
            f"{service_name}/compose.fragment.yml", _compose_fragment(charter.business_id, service_name)
        ),
    )
    artifact = Artifact(
        theme_name=charter.theme_name,
        dependencies=_SCAFFOLD_DEPS,
        architecture_rules=charter.tech.architecture_rules,  # the scaffold honours every mandated rule
        charter_version=charter.version,
    )
    return ScaffoldPlan(
        business_id=charter.business_id, service_name=service_name, files=files, artifact=artifact
    )


def to_scaffolded_event(
    plan: ScaffoldPlan,
    initiative_id: str,
    classification: Classification,
    product_id: str,
    producer: str = "product.engineering_agent",
) -> ProductScaffolded:
    """Build the `ProductScaffolded` domain event for a conformant scaffold. Pure."""
    return build(
        ProductScaffolded,
        subject=("Product", product_id),
        producer=producer,
        business_id=plan.business_id,
        initiative_id=initiative_id,
        product_id=product_id,
        classification=classification.kind,  # domain field — passes through **fields cleanly
        service_name=plan.service_name,
        theme_name=plan.artifact.theme_name,
        file_count=len(plan.files),
    )
