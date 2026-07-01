# Observability

A deterministic query layer over the ledger: per-business health snapshots, a fleet overview, cost attribution, and threshold-based anomaly detection.

## Language

**Fleet Overview**:
The whole portfolio at a glance — every business's revenue, spend, profit, and verdict, plus aggregates.
_Avoid_: dashboard, report (a Report is a generated artifact)

**Snapshot**:
One business's health at a point in time, attributed from the ledger and rolled into unit economics.
_Avoid_: status, view

**Anomaly**:
A flagged breach of a deterministic threshold (e.g. LLM cost too high, operating loss beyond a floor).
_Avoid_: alert, outlier (informally)
