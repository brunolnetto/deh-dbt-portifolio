select
    product_id,
    product_name,
    category,
    suggested_price,
    updated_at

from {{ ref('stg_produtos') }}
