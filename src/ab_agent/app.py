"""agent service — exposes POST /act to drive the gateway over HTTP.

Demonstrates the full chain across containers: client -> agent -> gateway ->
OPA/tool/audit/event. Mints its own token (interim issuer, ADR-0003) and calls
the gateway with a real httpx client.
"""

import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI

from ab_agent.runtime import record_decision
from ab_identity.tokens import issue_token

app = FastAPI(title="ab-agent")

GATEWAY_URL = os.environ.get("AB_GATEWAY_URL", "http://gateway:8000")
AGENT_ID = os.environ.get("AB_AGENT_ID", "executive.cmo_agent")


@app.post("/act")
def act() -> dict[str, Any]:
    token = issue_token(AGENT_ID)
    decision = {
        "decision_id": f"decision_{uuid.uuid4().hex[:8]}",
        "title": "Increase paid acquisition for Segment A",
        "authority_level": 3,
        "approval_status": "approved",
    }
    with httpx.Client(base_url=GATEWAY_URL, timeout=10.0) as client:
        resp = record_decision(client, token, decision)
    return {"gateway_status": resp.status_code, "decision_id": decision["decision_id"], "body": resp.json()}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
