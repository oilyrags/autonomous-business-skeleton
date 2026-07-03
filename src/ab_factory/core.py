"""Business Factory core — pure instantiation + gating logic (no I/O).

A business is provisioned from a `Blueprint` + capital, gated behind a readiness check, and
asked whether it may spend. The store wires real signals (ledger balance, kill-switch,
compliance) and persists; here everything is deterministic and injectable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ab_growth.blueprint import Blueprint
from ab_schemas.events import BusinessActivated, build


class Underfunded(Exception):
    """Provisioning was refused: capital is below the business's experiment budget."""


class Status(StrEnum):
    DRAFT = "draft"  # registered, capital may be allocated, but not yet cleared to act
    ACTIVE = "active"  # passed the readiness gate; may spend
    SUNSET = "sunset"  # stopped


@dataclass
class Business:
    blueprint: Blueprint
    capital_minor: int
    status: Status = Status.DRAFT

    @property
    def business_id(self) -> str:
        return self.blueprint.business_id

    @property
    def name(self) -> str:
        return self.blueprint.name

    @property
    def experiment_budget_minor(self) -> int:
        return self.blueprint.experiment_budget_minor


@dataclass(frozen=True)
class Readiness:
    ready: bool
    reasons: tuple[str, ...]  # why it is NOT ready; empty when ready


def readiness(
    business: Business,
    *,
    cash_balance: int,
    kill_switch_clear: bool,
    compliance_clear: bool,
) -> Readiness:
    """A business may launch only if funded, not killed, and compliant. Pure + injectable."""
    reasons: list[str] = []
    if cash_balance < business.experiment_budget_minor:
        reasons.append(f"capital {cash_balance} below experiment budget {business.experiment_budget_minor}")
    if not kill_switch_clear:
        reasons.append("kill switch active")
    if not compliance_clear:
        reasons.append("compliance (lawful-basis / RoPA) not clear")
    return Readiness(ready=not reasons, reasons=tuple(reasons))


@dataclass(frozen=True)
class SpendDecision:
    allowed: bool
    reason: str


def can_spend(business: Business, amount_minor: int, *, cash_balance: int) -> SpendDecision:
    """A business may spend only if it is active, the amount is positive, and it has the runway."""
    if business.status is not Status.ACTIVE:
        return SpendDecision(False, f"business not active (status {business.status})")
    if amount_minor <= 0:
        return SpendDecision(False, "amount must be positive")
    if amount_minor > cash_balance:
        return SpendDecision(False, f"insufficient runway: {amount_minor} > cash {cash_balance}")
    return SpendDecision(True, "ok")


def activate(business: Business, readiness: Readiness) -> Business:
    """Flip a draft business to active iff it passed the readiness gate; else leave it draft."""
    if readiness.ready and business.status is Status.DRAFT:
        business.status = Status.ACTIVE
    return business


def provision(blueprint: Blueprint, capital_minor: int) -> Business:
    """Create a draft business. Refuses an underfunded request (nothing is created)."""
    if capital_minor < blueprint.experiment_budget_minor:
        raise Underfunded(
            f"{blueprint.business_id}: capital {capital_minor} < experiment budget "
            f"{blueprint.experiment_budget_minor}"
        )
    return Business(blueprint=blueprint, capital_minor=capital_minor, status=Status.DRAFT)


def to_event(business: Business, producer: str = "executive.portfolio_agent") -> BusinessActivated:
    """The business-scoped activation event (published by the store when a business goes live)."""
    return build(
        BusinessActivated,
        subject=("Business", business.business_id),
        producer=producer,
        business_id=business.business_id,
        name=business.name,
        capital_minor=business.capital_minor,
    )
