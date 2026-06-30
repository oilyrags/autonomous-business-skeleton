"""audit service HTTP API: read the trail and check chain integrity."""

from typing import Any

from fastapi import FastAPI

from ab_audit import store

app = FastAPI(title="ab-audit")


@app.get("/audit")
def get_audit(principal: str | None = None, action: str | None = None) -> list[dict[str, Any]]:
    return store.read(principal=principal, action=action)


@app.get("/audit/verify")
def verify() -> dict[str, bool]:
    return {"intact": store.verify_chain()}
