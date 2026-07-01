"""Deterministic reliability controls: error budget, release freeze, and incident response.

An incident during a release must be *contained* by code, not judgement: a Sev1 auto-rolls
back to the last good version and freezes further releases; releases are also frozen when the
error budget is exhausted; Sev1/Sev2 require a postmortem; anything that touched PII requires a
breach assessment (GDPR Art.33/34). No I/O, no wall-clock — fully testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    SEV1 = "sev1"  # critical: user-facing outage / data risk
    SEV2 = "sev2"
    SEV3 = "sev3"


class ReleaseFrozen(Exception):
    """A deploy was attempted while releases are frozen (error budget / active incident)."""


class NothingToRollBackTo(Exception):
    """A rollback was requested but there is no previous known-good version."""


@dataclass(frozen=True)
class ErrorBudget:
    """A window-based SLO error budget. budget = (1 - slo_target) * window (in requests)."""

    slo_target: float  # e.g. 0.99 → 1% of the window may error
    window: int

    @property
    def budget(self) -> int:
        return round((1.0 - self.slo_target) * self.window)

    def remaining(self, errors: int) -> int:
        return self.budget - errors

    def exhausted(self, errors: int) -> bool:
        return errors > self.budget


@dataclass(frozen=True)
class Incident:
    id: str
    severity: Severity
    touched_pii: bool
    summary: str = ""


@dataclass
class ReleaseManager:
    """Tracks the deployed version + the previous known-good, and the freeze flag."""

    current: str
    previous: str | None = None
    frozen: bool = False

    def deploy(self, version: str) -> None:
        if self.frozen:
            raise ReleaseFrozen(f"cannot deploy {version}: releases are frozen")
        self.previous = self.current
        self.current = version

    def rollback(self) -> str:
        if self.previous is None:
            raise NothingToRollBackTo(f"no previous version to roll back to from {self.current}")
        self.current = self.previous
        return self.current

    def freeze(self) -> None:
        self.frozen = True

    def can_release(self, budget: ErrorBudget | None = None, errors: int = 0) -> bool:
        return not self.frozen and not (budget is not None and budget.exhausted(errors))


@dataclass(frozen=True)
class IncidentResponse:
    rolled_back: bool
    rolled_back_to: str | None
    release_frozen: bool
    postmortem_required: bool
    breach_assessment_required: bool


def handle_incident(
    incident: Incident,
    release: ReleaseManager,
    budget: ErrorBudget | None = None,
    errors: int = 0,
) -> IncidentResponse:
    """Contain an incident: Sev1 → auto-rollback + freeze; error-budget burn → freeze; Sev1/Sev2
    → postmortem; PII touched → breach assessment. Mutates the release (rollback/freeze)."""
    rolled_back = False
    rolled_back_to: str | None = None
    if incident.severity == Severity.SEV1:
        rolled_back_to = release.rollback()
        rolled_back = True

    frozen = incident.severity == Severity.SEV1 or (budget is not None and budget.exhausted(errors))
    if frozen:
        release.freeze()

    return IncidentResponse(
        rolled_back=rolled_back,
        rolled_back_to=rolled_back_to,
        release_frozen=frozen,
        postmortem_required=incident.severity in {Severity.SEV1, Severity.SEV2},
        breach_assessment_required=incident.touched_pii,
    )
