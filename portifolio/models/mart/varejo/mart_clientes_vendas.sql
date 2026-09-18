{{ config(tags=['marts', 'varejo']) }}

select
    c.customer_id,
    c.customer_name,
    c.state,
    c.state_name,
    c.region,
    c.segment,
    coalesce(v.total_sales, 0)          as total_sales,
    coalesce(v.paid_sales, 0)           as paid_sales,
    coalesce(v.cancelled_sales, 0)      as cancelled_sales,
    coalesce(v.refunded_sales, 0)       as refunded_sales,
    coalesce(v.revenue, 0)              as revenue,
    coalesce(v.refunded_amount, 0)      as refunded_amount,
    v.avg_paid_sale,
    v.first_sale_date,
    v.last_sale_date

from {{ ref('dim_clientes') }} c
left join {{ ref('int_vendas_por_cliente') }} v
    on c.customer_id = v.customer_id
