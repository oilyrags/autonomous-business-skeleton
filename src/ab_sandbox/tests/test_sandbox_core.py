"""Tool sandbox: deny-by-default capability enforcement + full audit (pure, infra-free)."""

from __future__ import annotations

from ab_sandbox.core import Capability, SandboxPolicy, StubSandbox, ToolInvocation, evaluate


def _policy(*caps: Capability) -> SandboxPolicy:
    return SandboxPolicy(allowed_capabilities=frozenset(caps))


def _inv(*caps: Capability, tool: str = "fetch_url") -> ToolInvocation:
    return ToolInvocation(principal="growth.agent", tool=tool, capabilities=frozenset(caps))


def test_a_tool_within_policy_is_permitted() -> None:
    d = evaluate(_inv(Capability.NETWORK), _policy(Capability.NETWORK, Capability.FILESYSTEM))
    assert d.permitted is True and d.denied == frozenset()


def test_a_capability_outside_policy_is_denied() -> None:
    d = evaluate(_inv(Capability.NETWORK, Capability.SUBPROCESS), _policy(Capability.NETWORK))
    assert d.permitted is False
    assert d.denied == frozenset({Capability.SUBPROCESS})
    assert "subprocess" in d.reason


def test_deny_by_default_empty_policy_permits_nothing() -> None:
    assert evaluate(_inv(Capability.NETWORK), _policy()).permitted is False


def test_sandbox_audits_every_invocation() -> None:
    sandbox = StubSandbox(_policy(Capability.NETWORK))
    sandbox.execute(_inv(Capability.NETWORK, tool="fetch"))  # permitted
    sandbox.execute(_inv(Capability.SUBPROCESS, tool="shell"))  # denied
    assert [(a.tool, a.permitted) for a in sandbox.audit] == [("fetch", True), ("shell", False)]
