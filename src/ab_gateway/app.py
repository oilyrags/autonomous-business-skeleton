"""gateway service — the single ingress for agent tool calls.

Flow per call: validate token -> kill-switch check (fail-closed) -> (stub) model
-> OPA authorize -> dispatch tool -> audit -> emit domain event. Every outcome,
allow or deny, is audited.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from ab_audit import store as audit
from ab_common import bus, db
from ab_common.config import settings
from ab_gateway import model_gateway, opa, tools
from ab_identity import revocation
from ab_identity.tokens import InvalidToken, validate_token
from ab_killswitch import state
from ab_schemas.events import AgentDecisionMade, ApprovalStatus, DataClassification, SubjectRef
from ab_schemas.models import ToolCallRequest, ToolCallResult


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    db.init_db()
    bus.ensure_topic(settings.decision_topic)
    yield


app = FastAPI(title="ab-gateway", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> list[dict[str, object]]:
    """Discover the governed tool catalog (name + contract). Authorization is still
    enforced per call (OPA + untrusted-input gate); this only advertises what exists."""
    return [
        {"name": s.name, "side_effect": s.side_effect, "sensitive": s.sensitive, "description": s.description}
        for s in tools.REGISTRY.values()
    ]


def _deny(principal: str, action: str, resource: str, reason: str, status: int) -> JSONResponse:
    audit.append(principal, action, resource, "deny", {"reason": reason})
    return JSONResponse(
        status_code=status, content=ToolCallResult(status="denied", reason=reason).model_dump()
    )


@app.post("/tool-call")
def tool_call(
    req: ToolCallRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    # 1. Authenticate.
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    try:
        principal = validate_token(token)
    except InvalidToken as exc:
        return JSONResponse(
            status_code=401,
            content=ToolCallResult(status="denied", reason=f"invalid token: {exc}").model_dump(),
        )

    resource = str(req.args.get("decision_id", req.tool))

    # 2. Revocation (source of truth in identity, outside the gateway).
    if revocation.is_revoked(principal):
        return _deny(principal, req.tool, resource, "credential revoked", 403)

    # 3. Kill switch (fail-closed: deny if state can't be read).
    try:
        killed = state.is_killed(principal)
    except Exception:  # noqa: BLE001 - any failure to read state must fail closed
        killed = True
    if killed:
        return _deny(principal, req.tool, resource, "kill switch active", 403)

    # 3. Reason via the (stub) model — boundary exercised, output not used for the decision.
    model_gateway.complete("executive_reasoning", f"about to {req.tool} for {resource}")

    # 4. Authorize (default-deny).
    if not opa.authorize(principal, req.tool, resource, req.purpose):
        return _deny(principal, req.tool, resource, "not authorized by policy", 403)

    # 5. Resolve the tool against the registry (unregistered tools are uncallable).
    spec = tools.get(req.tool)
    if spec is None:
        return _deny(principal, req.tool, resource, "unknown tool", 400)

    # 5a. Prompt-injection defense: a sensitive tool fails closed on an untrusted-input flow,
    #     even though policy allowed it above (defense in depth, architecture/10).
    if tools.blocked_by_input_trust(spec, untrusted_input=req.untrusted_input):
        return _deny(principal, req.tool, resource, "sensitive tool blocked under untrusted-input flow", 403)

    # 5b. Dispatch (deterministic side-effect).
    decision_id = spec.handler(principal, req.args)

    # 6. Audit the allowed action.
    audit.append(principal, req.tool, decision_id, "allow", {"tool": req.tool})

    # 7. Emit the domain event.
    event = AgentDecisionMade(
        event_name="AgentDecisionMade",
        event_id=str(uuid4()),
        occurred_at=datetime.now(tz=UTC),
        producer=principal,
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=SubjectRef(type="Decision", id=decision_id),
        decision_id=decision_id,
        agent_id=principal,
        authority_level=int(req.args.get("authority_level", 0)),
        approval_status=ApprovalStatus(req.args.get("approval_status", "autonomous_within_policy")),
    )
    bus.publish(settings.decision_topic, key=decision_id, value=event.model_dump_json(by_alias=True))

    return JSONResponse(
        status_code=200,
        content=ToolCallResult(status="ok", decision_id=decision_id).model_dump(),
    )
