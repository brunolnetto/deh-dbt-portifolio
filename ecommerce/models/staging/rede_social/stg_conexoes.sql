select
    seguidor_id                             as follower_id,
    seguido_id                              as followed_id,
    cast(forca_conexao as numeric(5, 2))    as connection_strength,
    cast(data_conexao as date)              as connected_at,
    cast(updated_at as timestamp)           as updated_at

from {{ source('landing_rede_social', 'conexoes') }}
