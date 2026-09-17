{{ config(
    materialized='incremental',
    unique_key='sale_id',
    incremental_strategy='merge'
) }}

select
    sale_id,
    customer_id,
    product_id,
    sale_date,
    status,
    quantity,
    total_amount,

    case when status = 'pago'      then 1 else 0 end    as is_paid,
    case when status = 'cancelado' then 1 else 0 end    as is_cancelled,
    case when status = 'devolvido' then 1 else 0 end    as is_refunded,

    {{ amount_for_status('total_amount', 'status', 'pago') }}      as recognized_revenue,
    {{ amount_for_status('total_amount', 'status', 'devolvido') }} as refunded_amount,

    created_at,
    updated_at

from {{ ref('stg_vendas') }}

{% if is_incremental() %}
where updated_at > (
    select coalesce(max(updated_at), '1900-01-01'::timestamp)
    from {{ this }}
)
{% endif %}
