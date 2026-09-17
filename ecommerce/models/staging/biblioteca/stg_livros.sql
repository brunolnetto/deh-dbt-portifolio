select
    livro_id,
    trim(titulo)                        as title,
    trim(isbn)                          as isbn,
    ano_publicacao                      as publication_year,
    quantidade_disponivel               as available_copies,
    cast(updated_at as timestamp)       as updated_at

from {{ source('biblioteca', 'livro') }}
