"""Activate the kill switch: set a control flag, revoke (agent scope), publish
``KillSwitchActivated``, and audit the activation. The launch-blocker control.
"""

from datetime import UTC, datetime

from ab_audit import store as audit
from ab_common import bus, db
from ab_common.config import settings
from ab_identity import revocation
from ab_schemas.events import DataClassification, KillSwitchActivated, KillSwitchScope, build


def activate(scope: str, target_id: str | None, reason: str, activated_by: str = "operator") -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO kill_switch (scope, target_id, active, reason, activated_by) "
            "VALUES (%s, %s, true, %s, %s)",
            (scope, target_id, reason, activated_by),
        )
        conn.commit()

    # Agent scope also revokes the principal (defence in depth).
    if scope == "agent" and target_id:
        revocation.revoke(target_id)

    audit.append(
        activated_by,
        "killswitch.activate",
        target_id or "global",
        "allow",
        {"scope": scope, "reason": reason},
    )

    now = datetime.now(tz=UTC)
    event = build(
        KillSwitchActivated,
        subject=("System", target_id or "global"),
        producer="security.killswitch",
        data_classification=DataClassification.CONFIDENTIAL,
        scope=KillSwitchScope(scope),
        target_id=target_id,
        reason=reason,
        activated_by=activated_by,
        activated_at=now,
    )
    bus.ensure_topic(settings.kill_topic)
    bus.publish_event(settings.kill_topic, key=target_id or "global", event=event)
