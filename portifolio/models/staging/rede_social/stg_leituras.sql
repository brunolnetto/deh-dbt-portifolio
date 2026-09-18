select
    pessoa_id,
    livro_id,
    cast(nota as numeric(3, 1))         as rating,
    cast(data_leitura as date)          as read_date,
    cast(updated_at as timestamp)       as updated_at

from {{ source('landing_rede_social', 'leituras') }}
