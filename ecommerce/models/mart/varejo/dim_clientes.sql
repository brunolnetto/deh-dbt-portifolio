select
    customer_id,
    customer_name,
    state,
    state_name,
    region,
    segment,
    registered_at,
    updated_at

from {{ ref('int_clientes_enriquecidos') }}
