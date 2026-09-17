{{ config(enabled=false) }}

    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'salespeople') }}
