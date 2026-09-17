select
    pessoa_id,
    livro_id,
    rating,
    read_date,
    updated_at

from {{ ref('stg_leituras') }}
