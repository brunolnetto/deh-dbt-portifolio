select
    l.livro_id,
    lr.title,
    lr.author,
    lr.publication_year,
    count(distinct l.pessoa_id)         as total_readers,
    round(avg(l.rating), 2)             as avg_rating,
    min(l.read_date)                    as first_read_date,
    max(l.read_date)                    as last_read_date,
    string_agg(
        distinct g.genre_name, ', '
        order by g.genre_name
    )                                   as genres

from {{ ref('stg_leituras') }} l
left join {{ ref('stg_livros_rede') }} lr
    on l.livro_id = lr.livro_id
left join {{ source('rede_social', 'livro_genero') }} lg
    on l.livro_id = lg.livro_id
left join {{ ref('stg_generos') }} g
    on lg.genero_id = g.genero_id
group by l.livro_id, lr.title, lr.author, lr.publication_year
