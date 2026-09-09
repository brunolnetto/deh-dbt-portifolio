select
    product_id,
    product_name,
    category,
    unit_price,
    is_active,
    created_at,
    updated_at,
    deleted_at
from {{ ref('stg_products') }}
