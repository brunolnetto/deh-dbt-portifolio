select
    id,
    service,
    method,
    endpoint,
    status_code,
    cast(duration_ms as numeric(10, 2))  as duration_ms,
    created_at

from {{ source('system', 'request_log') }}
