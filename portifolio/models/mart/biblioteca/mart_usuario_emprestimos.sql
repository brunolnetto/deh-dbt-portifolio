{{ config(tags=['marts', 'biblioteca']) }}

select
    u.usuario_id,
    u.user_name,
    u.user_type,
    u.email,
    coalesce(i.total_loans, 0)          as total_loans,
    coalesce(i.active_loans, 0)         as active_loans,
    coalesce(i.overdue_loans, 0)        as overdue_loans,
    coalesce(i.fined_loans, 0)          as fined_loans,
    coalesce(i.total_fines, 0)          as total_fines,
    i.first_loan_date,
    i.last_loan_date

from {{ ref('dim_usuarios') }} u
left join {{ ref('int_emprestimos_por_usuario') }} i
    on u.usuario_id = i.usuario_id
