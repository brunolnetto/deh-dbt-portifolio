select
    l.pessoa_id,
    p.person_name,
    p.age,
    count(*)                                as total_books_read,
    round(avg(l.rating), 2)                 as avg_rating,
    max(l.read_date)                        as last_read_date,
    string_agg(
        distinct g.genre_name, ', '
        order by g.genre_name
    )                                       as preferred_genres
from {{ ref('stg_leituras') }} l
left join {{ ref('stg_pessoas') }} p
    on l.pessoa_id = p.pessoa_id
left join {{ source('rede_social', 'pessoa_preferencia') }} pp
    on p.pessoa_id = pp.pessoa_id
left join {{ ref('stg_generos') }} g
    on pp.genero_id = g.genero_id
group by l.pessoa_id, p.person_name, p.age
