"""data service — the semantic layer as a running component.

A background thread continuously consumes AgentDecisionMade off the bus, appends
bronze, and rebuilds the medallion. The HTTP API serves canonical KPIs so other
contexts (e.g. Executive / decision intelligence) can query trusted metrics.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException

from ab_data import config, ingest, pipeline
from ab_data.metrics import REGISTRY, UnknownMetricError

_lock = threading.Lock()  # serialise warehouse access (duckdb single-writer)
_stop = threading.Event()


def _rebuild_loop() -> None:
    group = os.environ.get("AB_DATA_GROUP", "ab-data-service")
    while not _stop.is_set():
        try:
            landed = ingest.consume_to_bronze(group=group, max_messages=200, timeout=2.0)
            if landed and config.has_bronze():
                with _lock:
                    pipeline.build()
        except Exception:  # noqa: BLE001 - keep the loop alive across transient errors
            time.sleep(2)
        _stop.wait(1.0)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    thread = threading.Thread(target=_rebuild_loop, daemon=True)
    thread.start()
    yield
    _stop.set()


app = FastAPI(title="ab-data", lifespan=lifespan)


@app.get("/metrics")
def list_metrics() -> list[dict[str, str]]:
    return [
        {"name": n, "description": REGISTRY.get(n).description, "grain": REGISTRY.get(n).grain}
        for n in REGISTRY.names()
    ]


@app.get("/metrics/{name}")
def get_metric(name: str) -> dict[str, Any]:
    try:
        metric = REGISTRY.get(name)
    except UnknownMetricError as exc:
        raise HTTPException(status_code=404, detail=f"unknown metric: {name}") from exc

    dbpath = config.duckdb_path()
    if not dbpath.exists():
        return {"name": name, "value": None, "note": "warehouse not built yet"}
    with _lock:
        con = duckdb.connect(str(dbpath), read_only=True)
        try:
            row = con.sql(metric.sql).fetchone()
        finally:
            con.close()
    return {"name": name, "value": int(row[0]) if row else 0, "grain": metric.grain}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
