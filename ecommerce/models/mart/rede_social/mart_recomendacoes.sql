{{ config(tags=['marts', 'rede_social']) }}

-- Book recommendations: books read by connections that the person hasn't read yet,
-- ranked by avg_rating of connected readers and connection strength.
select
    target.pessoa_id,
    target.person_name,
    lp.livro_id,
    lp.title,
    lp.author,
    lp.avg_rating                                   as network_avg_rating,
    lp.total_readers                                as network_readers,
    round(avg(c.connection_strength), 2)            as avg_connection_strength,
    count(distinct c.follower_id)                   as recommended_by_count

from {{ ref('dim_pessoas') }} target

-- connections the person follows
join {{ ref('fct_conexoes') }} c
    on c.follower_id = target.pessoa_id

-- books read by their connections
join {{ ref('fct_leituras') }} cl
    on cl.pessoa_id = c.followed_id

-- book stats
join {{ ref('dim_livros_rede') }} lp
    on cl.livro_id = lp.livro_id

-- exclude books already read by the target person
where not exists (
    select 1
    from {{ ref('fct_leituras') }} tl
    where tl.pessoa_id = target.pessoa_id
      and tl.livro_id  = cl.livro_id
)

group by
    target.pessoa_id, target.person_name,
    lp.livro_id, lp.title, lp.author,
    lp.avg_rating, lp.total_readers

having count(distinct c.follower_id) >= 1

order by target.pessoa_id, network_avg_rating desc, recommended_by_count desc
