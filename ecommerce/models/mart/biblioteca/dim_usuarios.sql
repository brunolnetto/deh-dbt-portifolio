select
    usuario_id,
    user_name,
    user_type,
    email

from {{ ref('stg_usuarios') }}
