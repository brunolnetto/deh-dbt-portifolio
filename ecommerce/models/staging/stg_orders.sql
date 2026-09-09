select
    order_id,
    customer_id,
    salesperson_id,
    cast(order_date as date) as order_date,
    cast(amount as numeric(12, 2)) as amount,
    lower(trim(status)) as status,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'orders') }}
