select
    genero_id,
    trim(nome)                          as genre_name,
    cast(updated_at as timestamp)       as updated_at

from {{ source('rede_social', 'genero') }}
