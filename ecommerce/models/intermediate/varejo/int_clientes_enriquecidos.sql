select
    c.customer_id,
    c.customer_name,
    c.state,
    e.nome_estado    as state_name,
    e.regiao         as region,
    c.segment,
    c.registered_at,
    c.updated_at

from {{ ref('stg_clientes') }} c
left join {{ ref('estados_brasil') }} e
    on c.state = e.estado
