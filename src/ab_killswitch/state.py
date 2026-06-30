"""Kill-switch state — the gateway consults this on every tool call.

Reads the real control flags from Postgres. A principal is killed if a global
flag is active, or an agent-scoped flag targets that principal. Errors propagate
so the gateway can fail closed.
"""

from ab_common import db


def is_killed(principal: str) -> bool:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM kill_switch "
            "WHERE active AND (scope = 'global' OR (scope = 'agent' AND target_id = %s)) "
            "LIMIT 1",
            (principal,),
        ).fetchone()
    return row is not None
