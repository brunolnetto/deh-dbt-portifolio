select
    autor_id,
    trim(nome)                          as author_name,
    trim(nacionalidade)                 as nationality,
    cast(data_nascimento as date)       as birth_date,
    cast(updated_at as timestamp)       as updated_at

from {{ source('biblioteca', 'autor') }}
