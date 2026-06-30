"""Toolchain tracer test for slice 00.

Proves the schema package round-trips an AgentDecisionMade envelope. The expected
values are an independent hand-written literal (the AsyncAPI example), NOT recomputed
from the model — so the assertion can actually disagree with the code.
"""

from ab_schemas.events import AgentDecisionMade, DataClassification


def test_agent_decision_made_round_trips_asyncapi_example() -> None:
    # Independent literal: the AgentDecisionMade shape from events.asyncapi.yaml.
    raw = {
        "eventName": "AgentDecisionMade",
        "eventId": "3f1c0000-0000-4000-8000-000000000001",
        "occurredAt": "2026-06-30T10:00:00Z",
        "producer": "executive.cmo_agent",
        "schemaVersion": "1.0.0",
        "dataClassification": "confidential",
        "subjectRef": {"type": "Decision", "id": "decision_2026_001"},
        "decisionId": "decision_2026_001",
        "agentId": "executive.cmo_agent",
        "authorityLevel": 3,
        "approvalStatus": "approved",
    }

    event = AgentDecisionMade.model_validate(raw)

    assert event.event_name == "AgentDecisionMade"
    assert event.data_classification is DataClassification.CONFIDENTIAL
    assert event.subject_ref.type == "Decision"
    assert event.authority_level == 3
    assert event.art22_significant is False  # default applied

    # Round-trip back to the wire shape (camelCase aliases) preserves the envelope.
    dumped = event.model_dump(by_alias=True, mode="json")
    assert dumped["eventName"] == "AgentDecisionMade"
    assert dumped["subjectRef"] == {"type": "Decision", "id": "decision_2026_001"}
    assert dumped["authorityLevel"] == 3
