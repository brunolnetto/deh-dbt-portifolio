select
    e.emprestimo_id,
    e.usuario_id,
    e.livro_id,
    cast(e.data_emprestimo as date)            as loan_date,
    cast(e.data_devolucao_prevista as date)    as due_date,
    cast(e.data_devolucao_real as date)        as return_date,

    e.data_devolucao_real is not null          as is_returned,

    case
        when e.data_devolucao_real is not null
            then e.data_devolucao_real > e.data_devolucao_prevista
        else current_date > e.data_devolucao_prevista
    end                                        as is_overdue,

    case
        when e.data_devolucao_real is not null
            then greatest(0, e.data_devolucao_real - e.data_devolucao_prevista)
        when current_date > e.data_devolucao_prevista
            then current_date - e.data_devolucao_prevista
        else 0
    end                                        as days_overdue,

    m.valor_multa                              as fine_amount,
    coalesce(m.pago, false)                    as fine_paid,
    cast(e.updated_at as timestamp)            as updated_at

from {{ source('landing_biblioteca', 'emprestimos') }} e
left join {{ source('landing_biblioteca', 'multas') }} m
    on e.emprestimo_id = m.emprestimo_id
