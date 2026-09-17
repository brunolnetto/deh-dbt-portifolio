select
    produto_id                              as product_id,
    trim(nome_produto)                      as product_name,
    initcap(trim(categoria))                as category,
    cast(preco_sugerido as numeric(12, 2))  as suggested_price,
    cast(updated_at as timestamp)           as updated_at

from {{ source('varejo', 'origem_produto') }}
