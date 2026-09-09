select
    product_id,
    trim(name) as product_name,
    lower(trim(category)) as category,
    cast(unit_price as numeric(12, 2)) as unit_price,
    cast(is_active as boolean) as is_active,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'products') }}
