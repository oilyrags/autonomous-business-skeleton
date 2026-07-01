"""The publisher port: where a post goes live. A publish is outward-facing and effectively
irreversible, so it's a governed action (ADR-0054); the stub returns a deterministic platform post
id without touching the network, and a real Postiz / native-SDK adapter implements the same
``publish`` behind the interface.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from ab_social.core import Draft


class PublishResult(BaseModel):
    platform: str
    platform_post_id: str


class Publisher(Protocol):
    """Post (or schedule) a draft to its platform and return the platform's post id."""

    def publish(self, draft: Draft) -> PublishResult: ...


class StubPublisher:
    """Deterministic publisher for tests + the demo. A real Postiz/native adapter implements the
    same ``publish`` against the platform API."""

    def __init__(self) -> None:
        self._counter = 0

    def publish(self, draft: Draft) -> PublishResult:
        self._counter += 1
        return PublishResult(
            platform=draft.platform,
            platform_post_id=f"{draft.platform}_{draft.business_id}_{self._counter}",
        )
