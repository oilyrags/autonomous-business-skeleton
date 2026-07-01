-- Gold: decisions aggregated by calendar day (UTC) — the daily grain the semantic
-- layer serves as a time series. occurred_at is stored UTC-naive (see ingest._utc_naive).
{{ config(materialized='table') }}

select
    cast(date_trunc('day', occurred_at) as date) as day,
    count(*) as decision_count
from {{ ref('silver_decisions') }}
group by 1
order by 1
