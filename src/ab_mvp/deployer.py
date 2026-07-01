"""The deployer port: where a generated MVP page goes live. The stub returns a deterministic URL
without touching the network; a real adapter (Vercel/Netlify/container host) implements the same
``deploy`` — the MVP generator never changes.
"""

from __future__ import annotations

from typing import Protocol

from ab_mvp.core import Deployment, PageArtifact


class Deployer(Protocol):
    """Publish a page artifact and return where it went live."""

    def deploy(self, artifact: PageArtifact) -> Deployment: ...


class StubDeployer:
    """Deterministic deployer for tests + the demo: a stable stub URL per business, no network. A
    real Vercel/Netlify/container adapter implements the same ``deploy`` against its API."""

    def __init__(self, base_host: str = "mvp.stub.local") -> None:
        self._base_host = base_host

    def deploy(self, artifact: PageArtifact) -> Deployment:
        return Deployment(
            business_id=artifact.business_id,
            url=f"https://{artifact.business_id}.{self._base_host}/",
            content_hash=artifact.content_hash,
        )
