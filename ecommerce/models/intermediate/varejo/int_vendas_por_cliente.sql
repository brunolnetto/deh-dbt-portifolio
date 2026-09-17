select
    customer_id,
    count(*)                                                        as total_sales,
    {{ status_count('status', 'pago') }}                            as paid_sales,
    {{ status_count('status', 'cancelado') }}                       as cancelled_sales,
    {{ status_count('status', 'devolvido') }}                       as refunded_sales,
    sum(case when status = 'pago' then total_amount else 0 end)     as revenue,
    sum(case when status = 'devolvido' then total_amount else 0 end) as refunded_amount,
    avg(case when status = 'pago' then total_amount end)            as avg_paid_sale,
    min(sale_date)                                                  as first_sale_date,
    max(sale_date)                                                  as last_sale_date
from {{ ref('stg_vendas') }}
group by customer_id
