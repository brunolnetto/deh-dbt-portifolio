select
    salesperson_id,
    trim(name) as salesperson_name,
    lower(trim(email)) as email,
    initcap(trim(region)) as region,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at,
    cast(deleted_at as timestamp without time zone) as deleted_at
from {{ source('shop', 'salespeople') }}
