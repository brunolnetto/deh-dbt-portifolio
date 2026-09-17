"""Interactive BEFORE/AFTER observation tool.

Runs a mutation, triggers an incremental dbt build, and prints a side-by-side
diff of the affected OLTP and analytics rows.

Usage:
  python -m portfolio_api.observe <domain> <action>
  python -m portfolio_api.observe varejo insert-venda
  python -m portfolio_api.observe biblioteca insert-emprestimo
  python -m portfolio_api.observe rede_social insert-leitura --no-dbt
"""

import argparse
import os
import subprocess
import sys
from typing import Any

import psycopg
from dotenv import load_dotenv

load_dotenv()

_DSN = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5437')}"
    f"/{os.environ['POSTGRES_DB']}"
)

# ── Snapshot queries per domain/action ───────────────────────────────────────

_SNAPSHOTS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "varejo": {
        "insert-venda": [
            ("OLTP — origens_venda (5 mais recentes)",
             "SELECT venda_id, cliente_id, produto_id, data_venda, valor_total, status, updated_at::date FROM varejo.origem_venda ORDER BY venda_id DESC LIMIT 5"),
            ("ANALYTICS — fct_vendas (5 mais recentes)",
             "SELECT sale_id, customer_id, sale_date, total_amount, status, recognized_revenue FROM analytics_varejo.fct_vendas ORDER BY sale_id DESC LIMIT 5"),
        ],
        "update-venda": [
            ("OLTP — origens_venda (10 mais recentes por updated_at)",
             "SELECT venda_id, status, valor_total, updated_at FROM varejo.origem_venda ORDER BY updated_at DESC LIMIT 10"),
            ("ANALYTICS — fct_vendas (10 mais recentes por updated_at)",
             "SELECT sale_id, status, total_amount, updated_at FROM analytics_varejo.fct_vendas ORDER BY updated_at DESC LIMIT 10"),
        ],
        "update-cliente": [
            ("OLTP — clientes (10 mais recentes por updated_at)",
             "SELECT cliente_id, nome, segmento, updated_at FROM varejo.origem_cliente ORDER BY updated_at DESC LIMIT 10"),
            ("ANALYTICS — dim_clientes (10 mais recentes por updated_at)",
             "SELECT customer_id, customer_name, segment, updated_at FROM analytics_varejo.dim_clientes ORDER BY updated_at DESC LIMIT 10"),
        ],
        "insert-cliente": [
            ("OLTP — clientes (5 mais recentes)",
             "SELECT cliente_id, nome, estado, segmento, data_cadastro FROM varejo.origem_cliente ORDER BY cliente_id DESC LIMIT 5"),
            ("ANALYTICS — dim_clientes (5 mais recentes)",
             "SELECT customer_id, customer_name, state, segment FROM analytics_varejo.dim_clientes ORDER BY customer_id DESC LIMIT 5"),
        ],
        "late-venda": [
            ("OLTP — vendas mais antigas",
             "SELECT venda_id, data_venda, valor_total, status, updated_at::date FROM varejo.origem_venda ORDER BY data_venda ASC LIMIT 5"),
            ("ANALYTICS — fct_vendas mais antigas",
             "SELECT sale_id, sale_date, total_amount, status, updated_at::date FROM analytics_varejo.fct_vendas ORDER BY sale_date ASC LIMIT 5"),
        ],
        "simulate": [
            ("OLTP — resumo varejo",
             "SELECT count(*) as vendas, sum(valor_total) as receita_total, max(updated_at)::date as last_update FROM varejo.origem_venda"),
            ("ANALYTICS — resumo analytics_varejo.fct_vendas",
             "SELECT count(*) as sales, sum(total_amount) as revenue, max(updated_at)::date as last_update FROM analytics_varejo.fct_vendas"),
        ],
    },
    "biblioteca": {
        "insert-emprestimo": [
            ("OLTP — empréstimos ativos",
             "SELECT emprestimo_id, usuario_id, livro_id, data_emprestimo, data_devolucao_prevista FROM biblioteca.emprestimo WHERE data_devolucao_real IS NULL ORDER BY emprestimo_id DESC LIMIT 5"),
            ("ANALYTICS — fct_emprestimos ativos",
             "SELECT emprestimo_id, usuario_id, livro_id, loan_date, due_date, is_overdue FROM analytics_biblioteca.fct_emprestimos WHERE NOT is_returned ORDER BY emprestimo_id DESC LIMIT 5"),
        ],
        "return-livro": [
            ("OLTP — empréstimos recentemente devolvidos",
             "SELECT emprestimo_id, usuario_id, livro_id, data_devolucao_prevista, data_devolucao_real FROM biblioteca.emprestimo WHERE data_devolucao_real IS NOT NULL ORDER BY data_devolucao_real DESC LIMIT 5"),
            ("ANALYTICS — fct_emprestimos devolvidos (com atraso)",
             "SELECT emprestimo_id, loan_date, due_date, return_date, is_overdue, days_overdue, fine_amount FROM analytics_biblioteca.fct_emprestimos WHERE is_returned ORDER BY return_date DESC LIMIT 5"),
        ],
        "simulate": [
            ("OLTP — resumo biblioteca",
             "SELECT count(*) FILTER (WHERE data_devolucao_real IS NULL) as ativos, count(*) FILTER (WHERE current_date > data_devolucao_prevista AND data_devolucao_real IS NULL) as atrasados FROM biblioteca.emprestimo"),
            ("ANALYTICS — resumo analytics_biblioteca",
             "SELECT active_loans, overdue_loans, total_fines FROM analytics_biblioteca.fct_emprestimos JOIN LATERAL (SELECT sum(case when not is_returned then 1 end) as active_loans, sum(case when is_overdue then 1 end) as overdue_loans, coalesce(sum(fine_amount),0) as total_fines FROM analytics_biblioteca.fct_emprestimos) s ON true LIMIT 1"),
        ],
    },
    "rede_social": {
        "insert-leitura": [
            ("OLTP — leituras recentes",
             "SELECT pessoa_id, livro_id, nota, data_leitura FROM rede_social.leitura ORDER BY data_leitura DESC LIMIT 5"),
            ("ANALYTICS — fct_leituras recentes",
             "SELECT p.person_name, l.livro_id, l.rating, l.read_date FROM analytics_rede_social.fct_leituras l JOIN analytics_rede_social.dim_pessoas p ON l.pessoa_id=p.pessoa_id ORDER BY l.read_date DESC LIMIT 5"),
        ],
        "update-nota": [
            ("OLTP — leituras por updated_at",
             "SELECT pessoa_id, livro_id, nota, updated_at FROM rede_social.leitura ORDER BY updated_at DESC LIMIT 5"),
            ("ANALYTICS — fct_leituras por updated_at",
             "SELECT pessoa_id, livro_id, rating, updated_at FROM analytics_rede_social.fct_leituras ORDER BY updated_at DESC LIMIT 5"),
        ],
        "insert-conexao": [
            ("OLTP — conexões recentes",
             "SELECT seguidor_id, seguido_id, forca_conexao, data_conexao FROM rede_social.conexao_social ORDER BY data_conexao DESC LIMIT 5"),
            ("ANALYTICS — fct_conexoes recentes",
             "SELECT follower_id, followed_id, connection_strength, connected_at FROM analytics_rede_social.fct_conexoes ORDER BY connected_at DESC LIMIT 5"),
        ],
        "simulate": [
            ("OLTP — resumo rede_social",
             "SELECT (SELECT count(*) FROM rede_social.leitura) as leituras, (SELECT count(*) FROM rede_social.conexao_social) as conexoes"),
            ("ANALYTICS — resumo rede_social",
             "SELECT (SELECT count(*) FROM analytics_rede_social.fct_leituras) as fct_leituras, (SELECT count(*) FROM analytics_rede_social.fct_conexoes) as fct_conexoes"),
        ],
    },
}

# Default snapshot for unknown actions
_DEFAULT_SNAPSHOT = [("(sem snapshot para esta ação)", "SELECT 1 AS placeholder")]


def _run_query(conn, sql: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _print_table(title: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n  {title}")
    if not rows:
        print("    (nenhuma linha)")
        return
    cols = list(rows[0].keys())
    widths = [max(len(c), max((len(str(r.get(c, ""))) for r in rows), default=0)) for c in cols]
    header = " | ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep    = "-+-".join("-" * w for w in widths)
    print(f"    {header}")
    print(f"    {sep}")
    for row in rows:
        print("    " + " | ".join(str(row.get(c, "")).ljust(w) for c, w in zip(cols, widths)))


def _snapshot(conn, domain: str, action: str, label: str) -> dict[str, list[dict]]:
    queries = _SNAPSHOTS.get(domain, {}).get(action, _DEFAULT_SNAPSHOT)
    print(f"\n{'─' * 64}")
    print(f"  {label}")
    result = {}
    for title, sql in queries:
        try:
            rows = _run_query(conn, sql)
            _print_table(title, rows)
            result[title] = rows
        except Exception as exc:
            print(f"    (query indisponível: {exc})")
            result[title] = []
    return result


def _diff(before: dict, after: dict) -> None:
    print(f"\n{'═' * 64}")
    print("  DIFF (linhas novas ou alteradas)")
    print(f"{'═' * 64}")
    for title in after:
        b_rows = {str(r): r for r in before.get(title, [])}
        a_rows = {str(r): r for r in after.get(title, [])}
        added   = [r for k, r in a_rows.items() if k not in b_rows]
        changed = [r for k, r in a_rows.items() if k in b_rows and r != b_rows[k]]
        if added or changed:
            _print_table(f"Δ {title}", added + changed)
        else:
            print(f"\n  Δ {title}: sem mudanças detectadas na camada analytics")


def _run_dbt(domain: str) -> None:
    print(f"\n  Executando: dbt build --select tag:{domain} ...")
    result = subprocess.run(
        ["dbt", "build", "--select", f"tag:{domain}", "--profiles-dir", os.path.expanduser("~/.dbt")],
        cwd=os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ecommerce"),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Extract just the summary line
        for line in result.stdout.splitlines():
            if "Completed" in line or "Done." in line or "ERROR" in line:
                print(f"  {line.strip()}")
    else:
        print("  dbt build falhou:")
        print(result.stderr[-500:])


def main() -> None:
    parser = argparse.ArgumentParser(description="Observe OLTP mutation impact on the analytics layer")
    parser.add_argument("domain", choices=["varejo", "biblioteca", "rede_social"])
    parser.add_argument("action")
    parser.add_argument("--no-dbt", action="store_true", help="Skip dbt build (only show OLTP diff)")
    args = parser.parse_args()

    # Import CLI's action dispatcher to reuse the same mutation functions
    from .cli import _ACTIONS  # noqa: PLC0415
    actions = _ACTIONS.get(args.domain, {})
    if args.action not in actions:
        print(f"Unknown action '{args.action}'. Available: {', '.join(actions)}")
        sys.exit(1)

    with psycopg.connect(_DSN) as conn:
        before = _snapshot(conn, args.domain, args.action, "BEFORE")

        print(f"\n{'─' * 64}")
        print(f"  Aplicando: {args.domain} / {args.action}")
        with conn.cursor() as cur:
            actions[args.action](cur)
        conn.commit()

    if not args.no_dbt:
        _run_dbt(args.domain)

    with psycopg.connect(_DSN) as conn:
        after = _snapshot(conn, args.domain, args.action, "AFTER")

    _diff(before, after)
    print()


if __name__ == "__main__":
    main()
