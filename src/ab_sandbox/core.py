"""Tool execution sandboxing (deterministic): a tool runs only with the capabilities its policy
allows, and **every** invocation is audited. The sandbox is a port (`Sandbox`); the stub enforces a
capability allow-list without real isolation, and an E2B/Modal-style adapter slots in behind the
same interface. Deny-by-default: a capability not on the allow-list is refused before execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class Capability(StrEnum):
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    SUBPROCESS = "subprocess"
    ENV = "env"  # read process environment / secrets


@dataclass(frozen=True)
class SandboxPolicy:
    allowed_capabilities: frozenset[Capability]


@dataclass(frozen=True)
class ToolInvocation:
    principal: str
    tool: str
    capabilities: frozenset[Capability]


@dataclass(frozen=True)
class SandboxDecision:
    tool: str
    principal: str
    permitted: bool
    denied: frozenset[Capability]
    reason: str


def evaluate(invocation: ToolInvocation, policy: SandboxPolicy) -> SandboxDecision:
    """Permit a tool only if every capability it requests is on the policy allow-list (deny-by-
    default). Pure — the decision an adapter enforces before it runs anything."""
    denied = invocation.capabilities - policy.allowed_capabilities
    permitted = not denied
    reason = (
        "within policy" if permitted else f"capabilities not permitted: {sorted(c.value for c in denied)}"
    )
    return SandboxDecision(invocation.tool, invocation.principal, permitted, frozenset(denied), reason)


class Sandbox(Protocol):
    """Execute a tool under a capability policy, auditing every invocation."""

    def execute(self, invocation: ToolInvocation) -> SandboxDecision: ...


@dataclass
class StubSandbox:
    """Deterministic sandbox for tests + the demo: enforces the capability allow-list and records
    every invocation to an audit trail. A real E2B/Modal adapter enforces the same policy with true
    isolation, implementing the same ``execute``."""

    policy: SandboxPolicy
    audit: list[SandboxDecision] = field(default_factory=list)

    def execute(self, invocation: ToolInvocation) -> SandboxDecision:
        decision = evaluate(invocation, self.policy)
        self.audit.append(decision)  # every invocation is audited, permitted or denied
        return decision
