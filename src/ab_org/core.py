"""Hierarchical agent org (pure, deterministic): charters give each agent a role and an authority
level (the L0–L5 autonomy matrix); a decision that needs authority above the initiator's level
**escalates** up the reporting chain to the first agent who holds it — and to a human if no agent
does (so L5-restricted money/high-risk actions always reach a person). No LLM: routing is a
deterministic walk up ``reports_to``.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_AUTHORITY = 5  # L0–L5 autonomy matrix (architecture/06); L5 is restricted for money/high-risk


@dataclass(frozen=True)
class Charter:
    agent_id: str
    role: str
    authority_level: int  # 0..5, the highest-risk decision this agent may take autonomously
    department: str
    reports_to: str | None = None  # the agent it escalates to; None at the top


@dataclass(frozen=True)
class Org:
    charters: dict[str, Charter]


@dataclass(frozen=True)
class Routing:
    decider: str | None  # the agent who may decide; None when it must go to a human
    path: tuple[str, ...]  # agents traversed, initiator first
    escalated_to_human: bool


def route(org: Org, *, initiator: str, required_level: int) -> Routing:
    """Route a decision needing ``required_level`` authority. Walk up ``reports_to`` from the
    initiator to the first agent whose authority covers it; if the chain is exhausted, escalate to a
    human. Deterministic; cycle-safe."""
    path: list[str] = []
    seen: set[str] = set()
    current: str | None = initiator
    while current is not None and current not in seen:
        seen.add(current)
        charter = org.charters.get(current)
        if charter is None:
            break
        path.append(current)
        if charter.authority_level >= required_level:
            return Routing(decider=current, path=tuple(path), escalated_to_human=False)
        current = charter.reports_to
    return Routing(decider=None, path=tuple(path), escalated_to_human=True)


def team(org: Org, department: str) -> list[Charter]:
    """The charters in a department — a team, ordered by authority (most senior first)."""
    members = [c for c in org.charters.values() if c.department == department]
    return sorted(members, key=lambda c: (-c.authority_level, c.agent_id))
