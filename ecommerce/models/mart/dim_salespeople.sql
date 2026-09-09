select
    salesperson_id,
    salesperson_name,
    email,
    region,
    created_at,
    updated_at,
    deleted_at
from {{ ref('stg_salespeople') }}
