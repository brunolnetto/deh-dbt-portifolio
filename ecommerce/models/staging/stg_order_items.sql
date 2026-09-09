select
    order_item_id,
    order_id,
    product_id,
    quantity,
    cast(unit_price as numeric(12, 2)) as unit_price,
    cast(amount as numeric(12, 2)) as amount,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'order_items') }}
