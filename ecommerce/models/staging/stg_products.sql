{{ config(enabled=false) }}

    cast(is_active as boolean) as is_active,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'products') }}
