select
    pessoa_id,
    person_name,
    age,
    total_books_read,
    avg_rating,
    last_read_date,
    preferred_genres

from {{ ref('int_leituras_por_pessoa') }}
