-- Silver: typed, de-duplicated decision facts from the bronze landing Parquet.
-- One row per event_id (latest ingestion wins).
{{ config(materialized='table') }}

select
    decision_id,
    agent_id,
    authority_level,
    approval_status,
    occurred_at,
    data_classification,
    ingested_at
from read_parquet('{{ var("bronze_path") }}')
qualify row_number() over (partition by event_id order by ingested_at desc) = 1
