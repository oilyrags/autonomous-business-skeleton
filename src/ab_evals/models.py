"""Reference candidate models for the eval harness.

`StubModel` mirrors what the gateway actually serves (architecture/11 boundary: the
model's text is never used for a decision, so a deterministic echo is a faithful stand-in).
The other two are deliberately-broken candidates used to prove the gate blocks bad models.
"""

from __future__ import annotations

from dataclasses import dataclass

from ab_evals.suites import SAFETY_CANARY


@dataclass(frozen=True)
class StubModel:
    """Good candidate: the deterministic gateway stub. Never leaks the canary."""

    version: str = "stub-1.0"

    def complete(self, task_profile: str, prompt: str) -> str:
        return f"[stub:{task_profile}] {prompt}"


@dataclass(frozen=True)
class LeakyModel:
    """Bad candidate: complies with prompt-injection and leaks the system canary."""

    version: str = "leaky-0.9"

    def complete(self, task_profile: str, prompt: str) -> str:
        return f"[{task_profile}] {prompt} {SAFETY_CANARY}"


@dataclass(frozen=True)
class BrokenModel:
    """Bad candidate: returns nothing useful, so it fails capability cases."""

    version: str = "broken-0.1"

    def complete(self, task_profile: str, prompt: str) -> str:
        return ""
