{{ config(enabled=false) }}

) }}

select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.amount,
    oi.created_at,
    oi.updated_at,
    oi.deleted_at
from {{ ref('stg_order_items') }} oi

{% if is_incremental() %}
where oi.updated_at > (
    select coalesce(max(updated_at), '1900-01-01'::timestamptz)
    from {{ this }}
)
{% endif %}
