{{ config(enabled=false) }}

    cc.country_name,
    cc.region,
    cc.currency,
    c.created_at,
    c.updated_at,
    c.deleted_at

from {{ ref('stg_customers') }} as c
left join {{ ref('country_codes') }} as cc
    on c.country_code = cc.country_code

