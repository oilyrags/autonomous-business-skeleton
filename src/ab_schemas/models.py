"""Request/response + tool-arg models for the gateway and tools."""

from typing import Any

from pydantic import BaseModel, Field

from ab_schemas.events import DataClassification


class ToolCallRequest(BaseModel):
    """What an agent sends to the gateway."""

    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    purpose: str
    # True when the agent is acting on untrusted content (e.g. an inbound email/web page):
    # sensitive tools fail closed on such flows (prompt-injection defense, architecture/10).
    untrusted_input: bool = False
    # Sensitivity of the data being handled in this call. An egress tool may not transmit
    # data classified above its clearance (exfiltration control, architecture/09-10).
    data_classification: DataClassification = DataClassification.INTERNAL


class ToolCallResult(BaseModel):
    status: str  # "ok" | "denied"
    decision_id: str | None = None
    reason: str | None = None


class DecisionWrite(BaseModel):
    """Args for the ``decision_registry.write`` tool."""

    decision_id: str
    title: str
    authority_level: int = Field(ge=0, le=5)
    approval_status: str = "autonomous_within_policy"


class NotifyExternal(BaseModel):
    """Args for the ``notify.external`` egress tool."""

    notification_id: str
    recipient: str
    body: str
