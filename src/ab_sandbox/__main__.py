"""Tool sandbox demo (deterministic, no infra).

    uv run python -m ab_sandbox

Tools run under a capability allow-list: a tool asking for a capability the policy doesn't grant is
denied before execution, and every invocation is audited. A real E2B/Modal adapter enforces the same
policy with true isolation behind the Sandbox port.
"""

from __future__ import annotations

from ab_sandbox.core import Capability, SandboxPolicy, StubSandbox, ToolInvocation

POLICY = SandboxPolicy(allowed_capabilities=frozenset({Capability.NETWORK, Capability.FILESYSTEM}))
INVOCATIONS = [
    ToolInvocation("growth.agent", "fetch_landing_page", frozenset({Capability.NETWORK})),
    ToolInvocation("growth.agent", "write_report", frozenset({Capability.FILESYSTEM})),
    ToolInvocation("growth.agent", "run_shell", frozenset({Capability.SUBPROCESS})),
    ToolInvocation("growth.agent", "dump_secrets", frozenset({Capability.ENV, Capability.NETWORK})),
]


def main() -> int:
    sandbox = StubSandbox(POLICY)
    for inv in INVOCATIONS:
        d = sandbox.execute(inv)
        verdict = "PERMIT" if d.permitted else "DENY  "
        print(f"  [{verdict}] {d.tool:20} {d.reason}")
    print(f"\n  audited {len(sandbox.audit)} invocation(s) (every call, permitted or denied)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
