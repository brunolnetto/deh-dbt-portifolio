{{ config(enabled=false) }}

    country_name,
    region,
    currency,
    created_at,
    updated_at,
    deleted_at

from {{ ref('int_customers_enriched') }}
