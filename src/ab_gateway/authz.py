"""Principal authorization facts the gateway binds at the point of action (VULN-002 / VULN-003).

OPA answers "may this principal use this capability?" — but three security-relevant attributes used
to flow from the *caller's own request* unchecked: which ``business_id`` it acts for, the
``authority_level`` it claims, and the ``approval_status`` it asserts. This module is the deterministic,
default-deny source of truth for the first two, and the rule that agents may never self-approve.

Grants are seeded from the agent registry (``architecture/05_agent_registry.json``); a real
deployment loads them from OPA data / the registry per environment. An **unknown principal serves no
business and has authority ceiling 0** — so a new or spoofed identity can do nothing until granted.
"""

from __future__ import annotations

from dataclasses import dataclass

WILDCARD = "*"  # a portfolio/treasury principal that legitimately acts across all businesses


@dataclass(frozen=True)
class Grant:
    """What a principal is allowed: an authority ceiling and the businesses it may act for."""

    authority_ceiling: int  # the highest authority_level it may assert (0..5)
    businesses: frozenset[str]  # business_ids it may act for; {WILDCARD} = the whole portfolio


# Default-deny registry. Seeded to mirror the agent registry (executive.cmo_agent: authorityLevel 3);
# the skeleton's executive operator acts portfolio-wide. Scope narrower principals per deployment.
_GRANTS: dict[str, Grant] = {
    "executive.cmo_agent": Grant(authority_ceiling=3, businesses=frozenset({WILDCARD})),
    # Owns growth.experiment.create (PRD 0007); the growth operator acts across the portfolio.
    "growth.experiment_design_agent": Grant(authority_ceiling=3, businesses=frozenset({WILDCARD})),
    # Owns product.initiative.promote (PRD 0008); Product Engineering acts across the portfolio
    # (extend any business, mint new ones).
    "product.engineering_agent": Grant(authority_ceiling=3, businesses=frozenset({WILDCARD})),
}

_DENY = Grant(authority_ceiling=0, businesses=frozenset())

# Statuses an agent may set on its own decisions. Human-approval outcomes (approved/rejected) may
# only be set by the approval workflow keyed to an approver — never self-asserted by the agent.
_SELF_DECLARABLE = frozenset({"autonomous_within_policy", "pending"})
_SAFE_DEFAULT_STATUS = "autonomous_within_policy"


def grant_for(principal: str) -> Grant:
    return _GRANTS.get(principal, _DENY)


def serves_business(principal: str, business_id: str) -> bool:
    """True iff the principal is authorized to act for this business (wildcard or explicit grant)."""
    g = grant_for(principal)
    return WILDCARD in g.businesses or business_id in g.businesses


def authority_ceiling(principal: str) -> int:
    """The highest ``authority_level`` this principal may legitimately claim (0 for the unknown)."""
    return grant_for(principal).authority_ceiling


def exceeds_authority(principal: str, claimed_level: int) -> bool:
    """True iff the claimed authority_level is above what the principal is granted."""
    return claimed_level > authority_ceiling(principal)


def sanitize_approval_status(claimed: str) -> str:
    """Reduce an agent-declared approval_status to what an agent may assert. A self-declared
    human-approval outcome (approved/rejected) is downgraded to autonomous_within_policy — the agent
    cannot forge that a human signed off."""
    return claimed if claimed in _SELF_DECLARABLE else _SAFE_DEFAULT_STATUS
