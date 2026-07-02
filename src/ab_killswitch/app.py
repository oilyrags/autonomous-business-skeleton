"""killswitch service HTTP API: activate the kill switch.

Halting the fleet is a security-operator action, not something any mesh peer may do (VULN-004). The
endpoint requires a signed operator identity in a mutating role and records the *verified* caller as
`activated_by` — the request body cannot spoof it, and an agent (which lacks the operator secret)
cannot trip the switch. The SPIFFE mTLS mesh authenticates the transport; this authorizes the actor.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from ab_common import operator_identity
from ab_common.config import settings
from ab_killswitch import control

app = FastAPI(title="ab-killswitch")


class ActivateRequest(BaseModel):
    scope: str  # "global" | "agent"
    target_id: str | None = None
    reason: str


def require_security_operator(
    x_operator_id: Annotated[str | None, Header()] = None,
    x_operator_role: Annotated[str | None, Header()] = None,
    x_operator_sig: Annotated[str | None, Header()] = None,
) -> str:
    """Verify the signed operator identity and require a mutating role; return the verified id."""
    if not operator_identity.verify(
        x_operator_id, x_operator_role, x_operator_sig, settings.operator_auth_secret
    ):
        raise HTTPException(status_code=401, detail="operator authentication required")
    assert x_operator_id is not None and x_operator_role is not None  # verify() guaranteed non-null
    if x_operator_role not in operator_identity.MUTATING_ROLES:
        raise HTTPException(status_code=403, detail=f"role '{x_operator_role}' may not halt the fleet")
    return x_operator_id


@app.post("/activate")
def activate(
    req: ActivateRequest,
    operator_id: Annotated[str, Depends(require_security_operator)],
) -> dict[str, str]:
    control.activate(req.scope, req.target_id, req.reason, operator_id)  # verified actor, not the body
    return {"status": "activated", "scope": req.scope, "target_id": req.target_id or "global"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
