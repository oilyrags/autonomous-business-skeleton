"""Registered tools the gateway may dispatch. Unregistered tools are uncallable.

A tool's side-effect is deterministic code — never model output.
"""

from collections.abc import Callable
from typing import Any

from ab_common import db
from ab_schemas.models import DecisionWrite


def write_decision(principal: str, args: dict[str, Any]) -> str:
    """Persist a Decision; return its id. Idempotent on decision_id."""
    d = DecisionWrite.model_validate(args)
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO decisions (decision_id, title, agent_id, authority_level, approval_status) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (decision_id) DO NOTHING",
            (d.decision_id, d.title, principal, d.authority_level, d.approval_status),
        )
        conn.commit()
    return d.decision_id


TOOLS: dict[str, Callable[[str, dict[str, Any]], str]] = {
    "decision_registry.write": write_decision,
}
