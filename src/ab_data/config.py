"""Warehouse paths for the DuckDB + Parquet lakehouse-lite."""

import os
from pathlib import Path

# Repo-relative default; tests point this at a tmp dir.
WAREHOUSE_DIR = Path(os.environ.get("AB_WAREHOUSE_DIR", "warehouse"))

# The dbt project ships alongside this package.
DBT_PROJECT_DIR = Path(__file__).parent / "dbt_project"


def bronze_path(warehouse_dir: Path = WAREHOUSE_DIR) -> Path:
    return warehouse_dir / "bronze" / "agent_decisions.parquet"


def duckdb_path(warehouse_dir: Path = WAREHOUSE_DIR) -> Path:
    return warehouse_dir / "warehouse.duckdb"
