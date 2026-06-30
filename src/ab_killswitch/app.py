"""killswitch service HTTP API: activate the kill switch."""

from fastapi import FastAPI
from pydantic import BaseModel

from ab_killswitch import control

app = FastAPI(title="ab-killswitch")


class ActivateRequest(BaseModel):
    scope: str  # "global" | "agent"
    target_id: str | None = None
    reason: str
    activated_by: str = "operator"


@app.post("/activate")
def activate(req: ActivateRequest) -> dict[str, str]:
    control.activate(req.scope, req.target_id, req.reason, req.activated_by)
    return {"status": "activated", "scope": req.scope, "target_id": req.target_id or "global"}
