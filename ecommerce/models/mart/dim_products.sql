{{ config(enabled=false) }}

    is_active,
    created_at,
    updated_at,
    deleted_at
from {{ ref('stg_products') }}
