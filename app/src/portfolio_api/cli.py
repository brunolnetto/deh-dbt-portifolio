"""CLI entry point for manual OLTP mutations.

Usage:
  python -m portfolio_api.cli <domain> <action>

Domains and actions:
  varejo      insert-cliente  insert-venda  update-cliente  update-venda  late-venda  simulate
  biblioteca  insert-emprestimo  return-livro  simulate
  rede_social insert-leitura  insert-conexao  update-nota  simulate
"""

import argparse
import os
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()

_DSN = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5437')}"
    f"/{os.environ['POSTGRES_DB']}"
)

# Reuse the cursor-level functions from the sidecar — they are pure sync functions
from .mutator import (
    _varejo_insert_venda,
    _varejo_update_status,
    _varejo_update_segmento,
    _biblioteca_insert_emprestimo,
    _biblioteca_return_livro,
    _rede_insert_leitura,
    _rede_insert_conexao,
    _rede_update_nota,
)

import random
from datetime import datetime, timedelta

VALID_ESTADOS   = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE"]
VALID_SEGMENTOS = ["Ouro", "Prata", "Bronze"]


def _varejo_insert_cliente(cur):
    cur.execute(
        """
        INSERT INTO varejo.origem_cliente (cliente_id, nome, estado, segmento, data_cadastro)
        SELECT coalesce(max(cliente_id), 200) + 1, 'Cliente_Novo', %s, %s, current_date
        FROM varejo.origem_cliente
        RETURNING cliente_id
        """,
        (random.choice(VALID_ESTADOS), random.choice(VALID_SEGMENTOS)),
    )
    cid = cur.fetchone()[0]
    print(f"[varejo] cliente {cid} criado")


def _varejo_late_venda(cur):
    old_date = datetime.now() - timedelta(days=45)
    cur.execute("SELECT cliente_id FROM varejo.origem_cliente ORDER BY random() LIMIT 1")
    c = cur.fetchone()
    cur.execute("SELECT produto_id FROM varejo.origem_produto ORDER BY random() LIMIT 1")
    p = cur.fetchone()
    if not c or not p:
        return
    amount = round(random.uniform(50, 1000), 2)
    cur.execute(
        """
        INSERT INTO varejo.origem_venda
            (data_venda, produto_id, cliente_id, quantidade, valor_total, status, created_at, updated_at)
        VALUES (%s, %s, %s, 1, %s, 'pago', now(), now())
        RETURNING venda_id
        """,
        (old_date.date(), p[0], c[0], amount),
    )
    print(f"[varejo] late venda {cur.fetchone()[0]} criada (data={old_date.date()})")


_ACTIONS: dict[str, dict[str, any]] = {
    "varejo": {
        "insert-cliente": _varejo_insert_cliente,
        "insert-venda":   _varejo_insert_venda,
        "update-cliente": _varejo_update_segmento,
        "update-venda":   _varejo_update_status,
        "late-venda":     _varejo_late_venda,
        "simulate":       lambda cur: random.choice([
            _varejo_insert_venda, _varejo_update_status, _varejo_update_segmento,
        ])(cur),
    },
    "biblioteca": {
        "insert-emprestimo": _biblioteca_insert_emprestimo,
        "return-livro":      _biblioteca_return_livro,
        "simulate":          lambda cur: random.choice([
            _biblioteca_insert_emprestimo, _biblioteca_return_livro,
        ])(cur),
    },
    "rede_social": {
        "insert-leitura":  _rede_insert_leitura,
        "insert-conexao":  _rede_insert_conexao,
        "update-nota":     _rede_update_nota,
        "simulate":        lambda cur: random.choice([
            _rede_insert_leitura, _rede_insert_conexao, _rede_update_nota,
        ])(cur),
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="DEH Portfolio OLTP mutations")
    parser.add_argument("domain", choices=_ACTIONS)
    parser.add_argument("action")
    args = parser.parse_args()

    actions = _ACTIONS[args.domain]
    if args.action not in actions:
        print(f"Unknown action '{args.action}' for domain '{args.domain}'.")
        print(f"Available: {', '.join(actions)}")
        sys.exit(1)

    with psycopg.connect(_DSN) as conn:
        with conn.cursor() as cur:
            actions[args.action](cur)
        conn.commit()


if __name__ == "__main__":
    main()
