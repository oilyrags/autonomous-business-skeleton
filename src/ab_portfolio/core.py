"""Portfolio capital-allocation engine (pure, no I/O, recommend-only).

Given per-business performance + a portfolio budget, recommend a capital action per business,
recycling capital from losers into winners within the budget cap. Deterministic; no ledger
writes (capital moves are human-in-the-loop, architecture/06).
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ab_schemas.events import CapitalReallocationRecommended, DataClassification, SubjectRef

SUNSET_FLOOR = int(os.environ.get("AB_SUNSET_FLOOR", "-2"))
MIN_CONCLUSIVE = int(os.environ.get("AB_MIN_CONCLUSIVE", "3"))
INVEST_THRESHOLD = int(os.environ.get("AB_INVEST_THRESHOLD", "2"))
REINVEST_INCREMENT_MINOR = int(os.environ.get("AB_REINVEST_INCREMENT_MINOR", "100000"))


class Action(StrEnum):
    SUNSET = "sunset"  # conclusive loser → reclaim capital
    STARVE = "starve"  # net-negative but inconclusive → no new capital, on watch
    INVEST_MORE = "invest_more"  # conclusive winner → recommend more capital
    HOLD = "hold"  # neutral / inconclusive / winner-but-no-budget


class BusinessPerformance(BaseModel):
    business_id: str
    capital_minor: int = Field(ge=0)
    scale_count: int = Field(default=0, ge=0)
    pivot_count: int = Field(default=0, ge=0)
    kill_count: int = Field(default=0, ge=0)

    @property
    def score(self) -> int:
        return self.scale_count - self.kill_count

    @property
    def experiments(self) -> int:
        return self.scale_count + self.pivot_count + self.kill_count


@dataclass(frozen=True)
class Recommendation:
    business_id: str
    action: Action
    capital_delta: int  # +increment invest, −capital sunset, 0 otherwise
    reason: str


def allocate(
    performances: list[BusinessPerformance],
    *,
    portfolio_budget_minor: int,
    reinvest_increment_minor: int = REINVEST_INCREMENT_MINOR,
) -> list[Recommendation]:
    """Recommend a capital action per business, respecting the portfolio budget cap.

    Losers are sunset (freeing capital), winners are funded greedily by score while the freed +
    unused budget lasts; a winner that no longer fits is held. Output preserves input order.
    """
    decisions: dict[str, Recommendation] = {}
    winners: list[BusinessPerformance] = []
    reclaimed = 0
    for p in performances:
        if p.score <= SUNSET_FLOOR and p.experiments >= MIN_CONCLUSIVE:
            decisions[p.business_id] = Recommendation(
                p.business_id,
                Action.SUNSET,
                -p.capital_minor,
                f"conclusive loser (score {p.score}, {p.experiments} experiments)",
            )
            reclaimed += p.capital_minor
        elif p.score >= INVEST_THRESHOLD:
            winners.append(p)  # decided after we know the available capacity
        elif p.score < 0:
            decisions[p.business_id] = Recommendation(
                p.business_id, Action.STARVE, 0, f"net-negative (score {p.score}), on watch"
            )
        else:
            decisions[p.business_id] = Recommendation(
                p.business_id, Action.HOLD, 0, f"inconclusive (score {p.score})"
            )

    deployed = sum(p.capital_minor for p in performances)
    available = portfolio_budget_minor - (deployed - reclaimed)  # sunsets free capacity first
    for p in sorted(winners, key=lambda x: x.score, reverse=True):
        if available >= reinvest_increment_minor:
            decisions[p.business_id] = Recommendation(
                p.business_id,
                Action.INVEST_MORE,
                reinvest_increment_minor,
                f"conclusive winner (score {p.score})",
            )
            available -= reinvest_increment_minor
        else:
            decisions[p.business_id] = Recommendation(
                p.business_id,
                Action.HOLD,
                0,
                f"winner (score {p.score}), but portfolio budget exhausted",
            )
    return [decisions[p.business_id] for p in performances]


def to_events(
    recommendations: list[Recommendation], producer: str = "executive.portfolio_agent"
) -> list[CapitalReallocationRecommended]:
    """Business-scoped advisory events for a set of recommendations (for review, not execution)."""
    return [
        CapitalReallocationRecommended(
            event_name="CapitalReallocationRecommended",
            event_id=uuid.uuid4().hex,
            occurred_at=datetime.now(tz=UTC),
            producer=producer,
            data_classification=DataClassification.INTERNAL,
            subject_ref=SubjectRef(type="Business", id=r.business_id),
            business_id=r.business_id,
            action=r.action.value,
            capital_delta=r.capital_delta,
            reason=r.reason,
        )
        for r in recommendations
    ]
