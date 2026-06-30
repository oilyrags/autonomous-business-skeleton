"""identity service HTTP API: issue agent tokens."""

from fastapi import FastAPI
from pydantic import BaseModel

from ab_identity.tokens import issue_token

app = FastAPI(title="ab-identity")


class TokenRequest(BaseModel):
    agent_id: str


class TokenResponse(BaseModel):
    token: str


@app.post("/tokens", response_model=TokenResponse)
def create_token(req: TokenRequest) -> TokenResponse:
    return TokenResponse(token=issue_token(req.agent_id))
