"""identity service HTTP API: issue agent tokens."""

from fastapi import FastAPI
from pydantic import BaseModel

from ab_identity import revocation
from ab_identity.tokens import issue_token

app = FastAPI(title="ab-identity")


class TokenRequest(BaseModel):
    agent_id: str


class TokenResponse(BaseModel):
    token: str


class RevokeRequest(BaseModel):
    agent_id: str


@app.post("/tokens", response_model=TokenResponse)
def create_token(req: TokenRequest) -> TokenResponse:
    return TokenResponse(token=issue_token(req.agent_id))


@app.post("/revoke")
def revoke_agent(req: RevokeRequest) -> dict[str, str]:
    revocation.revoke(req.agent_id)
    return {"status": "revoked", "agent_id": req.agent_id}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
