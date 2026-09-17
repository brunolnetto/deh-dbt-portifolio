{{ config(enabled=false) }}

    created_at,
    updated_at,
    deleted_at
from {{ ref('stg_salespeople') }}
