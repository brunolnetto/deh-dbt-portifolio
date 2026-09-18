select
    cliente_id                       as customer_id,
    trim(nome)                       as customer_name,
    upper(trim(estado))              as state,
    initcap(trim(segmento))          as segment,
    cast(data_cadastro as date)      as registered_at,
    cast(updated_at as timestamp)    as updated_at

from {{ source('landing_varejo', 'clientes') }}
