{{ config(enabled=false) }}

    sum(oi.amount) as revenue,
    avg(oi.unit_price) as average_unit_price,
    min(oi.created_at) as first_sale_at,
    max(oi.created_at) as last_sale_at
from {{ ref('stg_order_items') }} oi
left join {{ ref('stg_products') }} p
    on oi.product_id = p.product_id
group by
    oi.product_id,
    p.product_name,
    p.category
