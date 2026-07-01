"""AgentDecisionMade carries an optional business_id (camelCase businessId on the wire)."""

from __future__ import annotations

from datetime import UTC, datetime

from ab_schemas.events import AgentDecisionMade, ApprovalStatus, DataClassification, SubjectRef


def _decision(**over: object) -> AgentDecisionMade:
    base: dict[str, object] = dict(
        event_name="AgentDecisionMade",
        event_id="e1",
        occurred_at=datetime(2026, 7, 2, tzinfo=UTC),
        producer="executive.cmo_agent",
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=SubjectRef(type="Decision", id="d1"),
        decision_id="d1",
        agent_id="executive.cmo_agent",
        authority_level=2,
        approval_status=ApprovalStatus.AUTONOMOUS_WITHIN_POLICY,
    )
    base.update(over)
    return AgentDecisionMade(**base)  # type: ignore[arg-type]


def test_business_id_defaults_to_none() -> None:
    assert _decision().business_id is None


def test_business_id_round_trips_as_camel_case() -> None:
    dumped = _decision(business_id="acme").model_dump_json(by_alias=True)
    assert '"businessId":"acme"' in dumped.replace(" ", "")
    assert AgentDecisionMade.model_validate_json(dumped).business_id == "acme"
