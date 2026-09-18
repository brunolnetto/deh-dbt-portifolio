select
    e.usuario_id,
    u.user_name,
    u.user_type,
    count(*)                                                    as total_loans,
    sum(case when not e.is_returned then 1 else 0 end)         as active_loans,
    sum(case when e.is_overdue then 1 else 0 end)              as overdue_loans,
    sum(case when e.fine_amount is not null then 1 else 0 end) as fined_loans,
    coalesce(sum(e.fine_amount), 0)                            as total_fines,
    min(e.loan_date)                                            as first_loan_date,
    max(e.loan_date)                                            as last_loan_date
from {{ ref('stg_emprestimos') }} e
left join {{ ref('stg_usuarios') }} u
    on e.usuario_id = u.usuario_id
group by e.usuario_id, u.user_name, u.user_type
