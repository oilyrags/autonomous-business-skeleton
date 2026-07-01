# Data

The analytics substrate: an event-fed warehouse with a freshness gate and the one canonical definition of each KPI.

## Language

**Data Product**:
An owned, contracted, discoverable dataset with SLA, lineage, classification, and quality tests.
_Avoid_: dataset, table (when you mean the governed product)

**Metric**:
The single canonical definition of a KPI (one definition per KPI, in the semantic layer).
_Avoid_: measure, number, stat

**Freshness**:
How current the warehouse is; a readiness gate refuses to serve KPIs when it is unbuilt or stale.
_Avoid_: recency, lag
