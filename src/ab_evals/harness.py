"""Offline eval harness for the model gateway (architecture/11 §5).

Eval sets are **code-defined** (like the metrics registry): each task profile has a set
of cases, each a deterministic ``check`` on a candidate model's output. Cases carry a
``dimension`` (capability / safety / grounding / regression) and a ``critical`` flag —
a critical failure (e.g. a jailbreak that leaks a canary) blocks promotion regardless of
the overall score. No LLM or infra: candidate models are plain callables, so the gate is
deterministic and unit-testable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol


class Model(Protocol):
    """A candidate model version: maps (task_profile, prompt) -> completion text."""

    @property
    def version(self) -> str: ...

    def complete(self, task_profile: str, prompt: str) -> str: ...


@dataclass(frozen=True)
class EvalCase:
    id: str
    dimension: str  # capability | safety | grounding | regression
    prompt: str
    check: Callable[[str], bool]  # True == the output is acceptable
    critical: bool = False  # a critical failure blocks promotion outright


@dataclass(frozen=True)
class FairnessCase:
    """A metamorphic bias case: the model is prompted once per protected-attribute group
    (same scenario otherwise) and ``fair`` checks the outputs are equivalent. Fairness can
    only be judged by *comparing* variants, so it needs its own paired case type."""

    id: str
    prompt_template: str  # must contain "{group}"
    groups: tuple[str, ...]  # protected-attribute values substituted in
    fair: Callable[[list[str]], bool]  # True == outputs are invariant to the group
    dimension: str = "bias"
    critical: bool = False


@dataclass(frozen=True)
class EvalSet:
    task_profile: str
    cases: tuple[EvalCase, ...]
    min_score: float  # required fraction of ALL cases passing (plus no critical fails)
    # Per-dimension minimum pass-rates, e.g. {"grounding": 1.0, "bias": 1.0}. A dimension
    # below its threshold blocks promotion — this is the design's per-profile grounding gate.
    thresholds: dict[str, float] = field(default_factory=dict)
    fairness: tuple[FairnessCase, ...] = ()
    # Significant automated decision (GDPR Art.22): such profiles MUST carry a bias eval.
    art22_significant: bool = False


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    dimension: str
    passed: bool
    critical: bool


@dataclass(frozen=True)
class EvalReport:
    task_profile: str
    model_version: str
    results: tuple[EvalResult, ...]

    @property
    def score(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def critical_failures(self) -> tuple[str, ...]:
        return tuple(r.case_id for r in self.results if r.critical and not r.passed)

    @property
    def failed_cases(self) -> tuple[str, ...]:
        return tuple(r.case_id for r in self.results if not r.passed)

    def dimensions(self) -> set[str]:
        return {r.dimension for r in self.results}

    def dimension_score(self, dimension: str) -> float | None:
        """Pass-rate within one dimension, or None if the set has no cases of it."""
        rs = [r for r in self.results if r.dimension == dimension]
        if not rs:
            return None
        return sum(1 for r in rs if r.passed) / len(rs)


def evaluate(model: Model, eval_set: EvalSet) -> EvalReport:
    """Run every case (and fairness case) in the set. Deterministic; no side effects."""
    results = []
    for case in eval_set.cases:
        try:
            passed = bool(case.check(model.complete(eval_set.task_profile, case.prompt)))
        except Exception:  # noqa: BLE001 - a model that errors on a case simply fails it
            passed = False
        results.append(EvalResult(case.id, case.dimension, passed, case.critical))
    for fc in eval_set.fairness:
        try:
            outputs = [
                model.complete(eval_set.task_profile, fc.prompt_template.format(group=g)) for g in fc.groups
            ]
            passed = bool(fc.fair(outputs))
        except Exception:  # noqa: BLE001
            passed = False
        results.append(EvalResult(fc.id, fc.dimension, passed, fc.critical))
    return EvalReport(eval_set.task_profile, model.version, tuple(results))
