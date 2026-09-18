select
    livro_id,
    title,
    author,
    publication_year,
    total_readers,
    avg_rating,
    first_read_date,
    last_read_date,
    genres

from {{ ref('int_livros_populares') }}
