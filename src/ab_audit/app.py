"""audit service HTTP API: read the trail, check chain integrity, and (in a
background thread) consume AgentDecisionMade to record receipt."""

import os
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from ab_audit import store
from ab_audit.consumer import consume_agent_decisions

_stop = threading.Event()


def _consume_loop() -> None:
    while not _stop.is_set():
        try:
            consume_agent_decisions(group="audit-service", max_messages=50, timeout=2.0)
        except Exception:  # noqa: BLE001 - keep the loop alive across transient errors
            time.sleep(1.0)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    thread: threading.Thread | None = None
    if os.environ.get("AB_AUDIT_CONSUMER", "0") == "1":
        thread = threading.Thread(target=_consume_loop, daemon=True)
        thread.start()
    yield
    _stop.set()


app = FastAPI(title="ab-audit", lifespan=lifespan)


@app.get("/audit")
def get_audit(principal: str | None = None, action: str | None = None) -> list[dict[str, Any]]:
    return store.read(principal=principal, action=action)


@app.get("/audit/verify")
def verify() -> dict[str, bool]:
    return {"intact": store.verify_chain()}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
