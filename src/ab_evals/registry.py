"""Promotion registry: which model version is cleared to serve each task profile.

The serving boundary consults this so an un-gated model is never served on a governed
path. In-memory for now (the design's model registry / MLflow is deferred).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PromotionRegistry:
    _promoted: dict[str, str] = field(default_factory=dict)  # task_profile -> model_version

    def promote(self, task_profile: str, model_version: str) -> None:
        self._promoted[task_profile] = model_version

    def promoted_version(self, task_profile: str) -> str | None:
        return self._promoted.get(task_profile)

    def is_promoted(self, task_profile: str) -> bool:
        return task_profile in self._promoted
