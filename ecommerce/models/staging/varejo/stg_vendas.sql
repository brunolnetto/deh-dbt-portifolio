select
    venda_id                                   as sale_id,
    cliente_id                                 as customer_id,
    produto_id                                 as product_id,
    cast(data_venda as date)                   as sale_date,
    quantidade                                 as quantity,
    cast(valor_total as numeric(12, 2))        as total_amount,
    lower(trim(status))                        as status,
    cast(created_at as timestamp)              as created_at,
    cast(updated_at as timestamp)              as updated_at

from {{ source('landing_varejo', 'vendas') }}
