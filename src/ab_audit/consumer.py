"""Consume AgentDecisionMade and record receipt in the audit log.

Deployment runs this as a loop; tests invoke it once. Records an
``event.received`` audit entry per consumed decision.
"""

import json

from ab_audit import store
from ab_common import bus
from ab_common.config import settings


def consume_agent_decisions(
    *, group: str, target_id: str | None = None, max_messages: int = 100, timeout: float = 10.0
) -> set[str]:
    """Consume up to ``max_messages`` events, recording receipt for each.

    Stops early once ``target_id`` is seen. Returns the set of decision ids seen.
    """
    seen: set[str] = set()
    for value in bus.consume(settings.decision_topic, group, max_messages=max_messages, timeout=timeout):
        payload = json.loads(value)
        decision_id = payload.get("decisionId")
        if not decision_id or decision_id in seen:
            continue
        seen.add(decision_id)
        store.append(
            payload.get("producer", "unknown"),
            "event.received",
            decision_id,
            "allow",
            {"event": payload.get("eventName")},
        )
        if target_id is not None and decision_id == target_id:
            break
    return seen
