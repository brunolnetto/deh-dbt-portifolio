select
    v.product_id,
    p.product_name,
    p.category,
    p.suggested_price,
    count(*)                                                as total_sales,
    sum(v.quantity)                                         as total_units_sold,
    sum(v.total_amount)                                     as revenue,
    avg(v.total_amount / nullif(v.quantity, 0))             as avg_unit_price,
    min(v.sale_date)                                        as first_sale_date,
    max(v.sale_date)                                        as last_sale_date
from {{ ref('stg_vendas') }} v
left join {{ ref('stg_produtos') }} p
    on v.product_id = p.product_id
group by
    v.product_id,
    p.product_name,
    p.category,
    p.suggested_price
