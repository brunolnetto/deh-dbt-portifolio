{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
  )
}}

-- One row per pipeline run event (dbt build via Cosmos, dlt ingestion cycle).
-- `extra` carries dag_id/task_id/run_id/duration_s/blob_path — see stg_app_logs.

select
    id,
    service,
    level,
    logger,
    message,
    extra ->> 'dag_id'                        as dag_id,
    extra ->> 'task_id'                       as task_id,
    extra ->> 'run_id'                        as run_id,
    (extra ->> 'duration_s')::numeric(10, 2)  as duration_s,
    extra ->> 'blob_path'                     as blob_path,
    created_at

from {{ ref('stg_app_logs') }}
where service in ('airflow-dbt', 'airflow-dlt')

{% if is_incremental() %}
and created_at > (select coalesce(max(created_at), '1900-01-01'::timestamptz) from {{ this }})
{% endif %}
