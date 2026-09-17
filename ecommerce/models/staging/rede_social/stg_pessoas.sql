select
    pessoa_id,
    trim(nome)                          as person_name,
    idade                               as age,
    cast(updated_at as timestamp)       as updated_at

from {{ source('rede_social', 'pessoa') }}
