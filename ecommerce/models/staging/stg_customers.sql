select
    customer_id,
    trim(name) as customer_name,
    lower(trim(email)) as email,
    upper(trim(country_code)) as country_code,
    cast(created_at as timestamp without time zone) as created_at,
    cast(updated_at as timestamp without time zone) as updated_at

from {{ source('shop', 'customers') }}

