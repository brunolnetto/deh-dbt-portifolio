select
    livro_id,
    title,
    isbn,
    publication_year,
    available_copies,
    authors,
    total_loans,
    active_loans

from {{ ref('int_livros_com_autores') }}
