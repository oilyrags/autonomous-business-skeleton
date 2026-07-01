-- Gold: decisions aggregated by agent (the shape the semantic layer serves).
{{ config(materialized='table') }}

select
    agent_id,
    count(*) as decision_count
from {{ ref('silver_decisions') }}
group by agent_id
