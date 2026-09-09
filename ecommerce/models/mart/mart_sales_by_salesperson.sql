{{ config(tags=['marts', 'sales']) }}

select
    s.salesperson_id,
    s.salesperson_name,
    s.region,
    coalesce(i.total_orders, 0) as total_orders,
    coalesce(i.revenue, 0) as revenue,
    coalesce(i.line_items, 0) as line_items,
    i.first_order_date,
    i.last_order_date
from {{ ref('dim_salespeople') }} s
left join {{ ref('int_sales_by_salesperson') }} i
    on s.salesperson_id = i.salesperson_id
