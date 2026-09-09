select
    o.salesperson_id,
    sp.salesperson_name,
    sp.region,
    count(distinct o.order_id) as total_orders,
    sum(o.amount) as revenue,
    count(*) as line_items,
    min(o.order_date) as first_order_date,
    max(o.order_date) as last_order_date
from {{ ref('stg_orders') }} o
left join {{ ref('stg_salespeople') }} sp
    on o.salesperson_id = sp.salesperson_id
where o.deleted_at is null
group by
    o.salesperson_id,
    sp.salesperson_name,
    sp.region
