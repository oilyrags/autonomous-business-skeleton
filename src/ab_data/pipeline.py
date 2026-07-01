"""Batch pipeline: land events -> dbt medallion -> quality + canonical metrics."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from ab_data import config, ingest, quality
from ab_data.metrics import REGISTRY
from ab_schemas.events import AgentDecisionMade


@dataclass
class PipelineResult:
    bronze_rows: int
    metrics: dict[str, int] = field(default_factory=dict)
    quality: list[quality.QualityResult] = field(default_factory=list)

    @property
    def quality_ok(self) -> bool:
        return quality.all_passed(self.quality)


def _dbt_build(warehouse_dir: Path) -> None:
    env = {**os.environ, "AB_WAREHOUSE_DB": str(config.duckdb_path(warehouse_dir))}
    proc = subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(config.DBT_PROJECT_DIR),
            "--profiles-dir",
            str(config.DBT_PROJECT_DIR),
            "--vars",
            json.dumps({"bronze_path": str(config.bronze_path(warehouse_dir))}),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"dbt build failed:\n{proc.stdout}\n{proc.stderr}")


def run(
    events: Sequence[AgentDecisionMade] | None = None,
    warehouse_dir: Path = config.WAREHOUSE_DIR,
) -> PipelineResult:
    """Run the full pipeline. Pass ``events`` to land them; otherwise bronze must exist."""
    if events is not None:
        ingest.write_bronze(events, warehouse_dir)

    _dbt_build(warehouse_dir)

    con = duckdb.connect(str(config.duckdb_path(warehouse_dir)), read_only=True)
    try:
        rows = con.sql("SELECT count(*) FROM silver_decisions").fetchone()
        bronze_rows = int(rows[0]) if rows else 0
        metrics: dict[str, int] = {}
        for name in REGISTRY.names():
            value = con.sql(REGISTRY.get(name).sql).fetchone()
            metrics[name] = int(value[0]) if value else 0
        checks = quality.run_checks(con)
    finally:
        con.close()

    return PipelineResult(bronze_rows=bronze_rows, metrics=metrics, quality=checks)
