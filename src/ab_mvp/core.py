"""MVP / landing-page generation (deterministic): a ``Blueprint`` becomes a page artifact with a
content hash, then a deployer port publishes it to a URL. No LLM — a deterministic template, so the
same blueprint always yields the same page (and hash). The hosting target lives behind
``ab_mvp.deployer.Deployer``.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel

from ab_growth.blueprint import Blueprint
from ab_schemas.events import DataClassification, MvpDeployed, SubjectRef


class PageArtifact(BaseModel):
    business_id: str
    html: str
    content_hash: str


class Deployment(BaseModel):
    business_id: str
    url: str
    content_hash: str


def _headline(blueprint: Blueprint) -> str:
    return f"{blueprint.name}: results without the busywork"


def render(blueprint: Blueprint) -> PageArtifact:
    """Generate a landing page from a Blueprint. Deterministic — same blueprint → same page/hash."""
    modules = "".join(f"<li>{m}</li>" for m in blueprint.enabled_modules)
    html = (
        '<!doctype html><html lang="en"><head>'
        f'<meta charset="utf-8"><title>{blueprint.name}</title></head><body>'
        f"<h1>{_headline(blueprint)}</h1>"
        f"<p>Early access for {blueprint.name}. Join the waitlist.</p>"
        f"<ul>{modules}</ul>"
        f'<form data-business="{blueprint.business_id}"><input name="email">'
        "<button>Get early access</button></form>"
        "</body></html>"
    )
    content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
    return PageArtifact(business_id=blueprint.business_id, html=html, content_hash=content_hash)


def to_event(deployment: Deployment, *, producer: str = "growth.mvp_agent") -> MvpDeployed:
    return MvpDeployed(
        event_name="MvpDeployed",
        event_id=uuid.uuid4().hex,
        occurred_at=datetime.now(tz=UTC),
        producer=producer,
        data_classification=DataClassification.INTERNAL,
        subject_ref=SubjectRef(type="Business", id=deployment.business_id),
        business_id=deployment.business_id,
        url=deployment.url,
        content_hash=deployment.content_hash,
    )


class DeployerLike(Protocol):
    """The slice ``deploy_mvp`` needs — any deployer (see ``deployer.Deployer``)."""

    def deploy(self, artifact: PageArtifact) -> Deployment: ...


def deploy_mvp(blueprint: Blueprint, deployer: DeployerLike) -> tuple[Deployment, MvpDeployed]:
    """Render the page from the blueprint, deploy it, and return the deployment + its event."""
    artifact = render(blueprint)
    deployment = deployer.deploy(artifact)
    return deployment, to_event(deployment)
