"""identity service HTTP API.

Token issuance now lives in Keycloak (ADR-0004); this service owns **revocation**
— the source of truth the gateway checks on every call (slice 03).
"""

from fastapi import FastAPI
from pydantic import BaseModel

from ab_identity import revocation

app = FastAPI(title="ab-identity")


class RevokeRequest(BaseModel):
    agent_id: str


@app.post("/revoke")
def revoke_agent(req: RevokeRequest) -> dict[str, str]:
    revocation.revoke(req.agent_id)
    return {"status": "revoked", "agent_id": req.agent_id}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
