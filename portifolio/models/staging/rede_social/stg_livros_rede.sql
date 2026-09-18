-- Prefixed to avoid conflicts with biblioteca.stg_livros
select
    livro_id,
    trim(titulo)                        as title,
    trim(autor)                         as author,
    ano_publicacao                      as publication_year,
    cast(updated_at as timestamp)       as updated_at

from {{ source('landing_rede_social', 'livros') }}
