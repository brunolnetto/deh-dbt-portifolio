-- Enriches books with aggregated author names and loan statistics
select
    l.livro_id,
    l.title,
    l.isbn,
    l.publication_year,
    l.available_copies,
    string_agg(a.author_name, ', ' order by a.author_name) as authors,
    count(distinct e.emprestimo_id)                         as total_loans,
    sum(case when not e.is_returned then 1 else 0 end)      as active_loans

from {{ ref('stg_livros') }} l
left join {{ source('biblioteca', 'livro_autor') }} la
    on l.livro_id = la.livro_id
left join {{ ref('stg_autores') }} a
    on la.autor_id = a.autor_id
left join {{ ref('stg_emprestimos') }} e
    on l.livro_id = e.livro_id
group by l.livro_id, l.title, l.isbn, l.publication_year, l.available_copies
