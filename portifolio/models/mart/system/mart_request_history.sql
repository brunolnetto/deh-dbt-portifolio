{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
  )
}}

select
    id,
    service,
    method,
    endpoint,
    status_code,
    round(duration_ms::numeric, 2) as duration_ms,
    created_at

from {{ ref('stg_request_logs') }}

{% if is_incremental() %}
where created_at > (select coalesce(max(created_at), '1900-01-01'::timestamptz) from {{ this }})
{% endif %}
