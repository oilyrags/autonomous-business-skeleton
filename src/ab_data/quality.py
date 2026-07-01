"""Data-quality checks on the modelled decisions (run after dbt builds gold)."""

from dataclasses import dataclass

import duckdb


@dataclass(frozen=True)
class QualityResult:
    check: str
    passed: bool
    detail: str


def run_checks(con: duckdb.DuckDBPyConnection) -> list[QualityResult]:
    """Freshness/completeness checks over the silver/gold models."""
    results: list[QualityResult] = []

    null_ids = con.sql("SELECT count(*) FROM silver_decisions WHERE decision_id IS NULL").fetchone()
    n_null = int(null_ids[0]) if null_ids else 0
    results.append(QualityResult("no_null_decision_id", n_null == 0, f"{n_null} null decision_id(s)"))

    # Gold totals must reconcile to silver (single-definition of "total").
    recon = con.sql(
        "SELECT (SELECT count(*) FROM silver_decisions) "
        "     - (SELECT coalesce(sum(decision_count), 0) FROM gold_decisions_by_agent)"
    ).fetchone()
    diff = int(recon[0]) if recon else 0
    results.append(QualityResult("gold_reconciles_to_silver", diff == 0, f"silver-gold diff = {diff}"))

    return results


def all_passed(results: list[QualityResult]) -> bool:
    return all(r.passed for r in results)
