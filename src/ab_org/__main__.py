"""Hierarchical org demo (deterministic, no infra).

    uv run python -m ab_org

Decisions route by required authority: an agent decides within its level, escalates up the chain
when it needs more, and reaches a human when an L5 (money/high-risk) action exceeds every agent.
"""

from __future__ import annotations

from ab_org.core import Charter, Org, route

ORG = Org(
    charters={
        "intern": Charter("intern", "Growth Intern", 1, "growth", reports_to="cmo"),
        "cmo": Charter("cmo", "CMO", 3, "growth", reports_to="ceo"),
        "ceo": Charter("ceo", "CEO", 4, "executive", reports_to=None),
    }
)


def main() -> int:
    for level, label in [(1, "tweak ad copy"), (3, "launch a campaign"), (5, "wire a large payment")]:
        r = route(ORG, initiator="intern", required_level=level)
        where = "HUMAN" if r.escalated_to_human else r.decider
        print(f"  L{level} '{label}': {' -> '.join(r.path)} -> [{where}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
