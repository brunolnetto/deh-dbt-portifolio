select
    usuario_id,
    trim(nome)                          as user_name,
    lower(trim(tipo))                   as user_type,
    lower(trim(email))                  as email,
    cast(updated_at as timestamp)       as updated_at

from {{ source('landing_biblioteca', 'usuarios') }}
