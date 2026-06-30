"""Kill-switch state — the gateway consults this on every tool call.

Slice 01 stub: nothing is killed. Slice 04 replaces this with real global /
per-agent control flags (fail-closed) backed by shared state, plus revocation
and the ``KillSwitchActivated`` broadcast.
"""


def is_killed(principal: str) -> bool:
    """Return True if the principal (or the system globally) is halted."""
    return False
