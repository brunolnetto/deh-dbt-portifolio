select
    service,
    date_trunc('hour', created_at)                                               as window_start,
    count(*)                                                                     as total_requests,
    count(*) filter (where status_code >= 400)                                   as error_requests,
    round(avg(duration_ms)::numeric, 2)                                          as avg_duration_ms,
    round(percentile_cont(0.95) within group (order by duration_ms)::numeric, 2) as p95_duration_ms,
    round(
        count(*) filter (where status_code >= 400) * 100.0
        / nullif(count(*), 0),
        2
    )                                                                            as error_rate_pct

from {{ ref('stg_request_logs') }}
group by 1, 2
order by 1, 2 desc
