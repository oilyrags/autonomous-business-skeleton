"""Data Platform & Intelligence context — the trusted data fabric (Phase 2).

Event -> bronze (Parquet) -> medallion (dbt-duckdb) -> gold -> semantic layer
(one canonical definition per KPI). See docs/adr/0012 and architecture/03 (Data
Platform) / 07 (data model) / 08 (data inventory).
"""
