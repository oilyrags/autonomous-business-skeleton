"""Reference candidate models for the eval harness.

`StubModel` mirrors what the gateway actually serves (architecture/11 boundary: the
model's text is never used for a decision, so a deterministic echo is a faithful stand-in).
The other two are deliberately-broken candidates used to prove the gate blocks bad models.
"""

from __future__ import annotations

import re
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


# --- reference behaviours for the Art.22 customer-facing profile (grounding + fairness) ---

_STOP = {"what", "which", "does", "your", "this", "that", "with", "from", "have"}


def _grounded_answer(prompt: str) -> str:
    """Answer only from an approved source that overlaps the question; else abstain.
    A minimal but real grounding policy — the point is *never fabricate*."""
    sources = re.findall(r"\[(\w+):([^\]]+)\]", prompt)  # [(id, text), ...]
    q = prompt.split("Q:", 1)[-1].lower()
    q_words = {w for w in re.findall(r"[a-z]{4,}", q) if w not in _STOP}
    for sid, text in sources:
        if q_words & set(re.findall(r"[a-z]{4,}", text.lower())):
            return f"Yes, based on [{sid}]: {text.strip()}"
    return "ABSTAIN: no approved source supports this question."


def _biased_group(prompt: str) -> str:
    return "Decision: DENY" if "group_b" in prompt else "Decision: APPROVE"


@dataclass(frozen=True)
class CompliantModel:
    """Good Art.22 candidate: grounded (cite-or-abstain) and fair (decision ignores group)."""

    version: str = "compliant-1.0"

    def complete(self, task_profile: str, prompt: str) -> str:
        if "SOURCES:" in prompt:
            return _grounded_answer(prompt)
        if "APPROVE or DENY" in prompt:
            return "Decision: APPROVE"  # based on income/credit only, not the group
        return f"[{task_profile}] {prompt}"


@dataclass(frozen=True)
class HallucinatingModel:
    """Bad Art.22 candidate: fabricates instead of grounding/abstaining."""

    version: str = "hallucinating-0.5"

    def complete(self, task_profile: str, prompt: str) -> str:
        if "SOURCES:" in prompt:
            return "The answer is 500000, definitely."  # ignores sources, invents a number
        if "APPROVE or DENY" in prompt:
            return "Decision: APPROVE"
        return f"[{task_profile}] {prompt}"


@dataclass(frozen=True)
class BiasedModel:
    """Bad Art.22 candidate: grounded, but its decision depends on the protected group."""

    version: str = "biased-0.7"

    def complete(self, task_profile: str, prompt: str) -> str:
        if "SOURCES:" in prompt:
            return _grounded_answer(prompt)  # passes grounding, so the block is attributable to bias
        if "APPROVE or DENY" in prompt:
            return _biased_group(prompt)
        return f"[{task_profile}] {prompt}"
