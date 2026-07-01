"""Warehouse paths for the DuckDB + Parquet lakehouse-lite.

Bronze is an append-only directory of Parquet parts (one per ingest batch), so the
long-running data service can accumulate events over time.
"""

import os
from pathlib import Path

# Repo-relative default; tests point this at a tmp dir, the container at /warehouse.
WAREHOUSE_DIR = Path(os.environ.get("AB_WAREHOUSE_DIR", "warehouse"))

# The dbt project ships alongside this package.
DBT_PROJECT_DIR = Path(__file__).parent / "dbt_project"


def bronze_dir(warehouse_dir: Path = WAREHOUSE_DIR) -> Path:
    return warehouse_dir / "bronze" / "agent_decisions"


def bronze_glob(warehouse_dir: Path = WAREHOUSE_DIR) -> str:
    return str(bronze_dir(warehouse_dir) / "*.parquet")


def duckdb_path(warehouse_dir: Path = WAREHOUSE_DIR) -> Path:
    return warehouse_dir / "warehouse.duckdb"


def has_bronze(warehouse_dir: Path = WAREHOUSE_DIR) -> bool:
    d = bronze_dir(warehouse_dir)
    return d.exists() and any(d.glob("*.parquet"))
