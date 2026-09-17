select
    genero_id,
    trim(nome)                          as genre_name,
    cast(updated_at as timestamp)       as updated_at

from {{ source('landing_rede_social', 'generos') }}
