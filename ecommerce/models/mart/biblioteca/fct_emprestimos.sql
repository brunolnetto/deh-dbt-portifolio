{{ config(
    materialized='incremental',
    unique_key='emprestimo_id',
    incremental_strategy='merge'
) }}

select
    emprestimo_id,
    usuario_id,
    livro_id,
    loan_date,
    due_date,
    return_date,
    is_returned,
    is_overdue,
    days_overdue,
    fine_amount,
    fine_paid,
    updated_at

from {{ ref('stg_emprestimos') }}

{% if is_incremental() %}
where updated_at > (
    select coalesce(max(updated_at), '1900-01-01'::timestamp)
    from {{ this }}
)
{% endif %}
