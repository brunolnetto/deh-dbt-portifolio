select
    id,
    service,
    level,
    logger,
    message,
    extra,
    created_at

from {{ source('system', 'app_log') }}
