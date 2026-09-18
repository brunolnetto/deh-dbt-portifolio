select
    follower_id,
    followed_id,
    connection_strength,
    connected_at,
    updated_at

from {{ ref('stg_conexoes') }}
