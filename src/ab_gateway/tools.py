"""Tool registry (architecture/11 §2): governed capabilities the gateway may dispatch.

Every tool carries a contract — a side-effect class and a sensitivity flag — alongside its
handler. Unregistered tools are uncallable. A tool's side-effect is deterministic code,
never model output. Sensitive tools **fail closed under untrusted-input flows** (`10`
prompt-injection defense): if the agent is acting on untrusted content, a sensitive tool is
refused even when policy would otherwise allow it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ab_common import db
from ab_schemas.models import DecisionWrite

Handler = Callable[[str, dict[str, Any]], str]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: Handler
    side_effect: str  # "read" | "write" | "irreversible"
    sensitive: bool  # blocked under untrusted-input flows (prompt-injection defense)
    description: str


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


REGISTRY: dict[str, ToolSpec] = {
    "decision_registry.write": ToolSpec(
        name="decision_registry.write",
        handler=write_decision,
        side_effect="write",
        sensitive=True,
        description="Persist an agent Decision to the registry.",
    ),
}


def get(name: str) -> ToolSpec | None:
    return REGISTRY.get(name)


def blocked_by_input_trust(spec: ToolSpec, *, untrusted_input: bool) -> bool:
    """Sensitive tools fail closed when the flow is processing untrusted input."""
    return untrusted_input and spec.sensitive
