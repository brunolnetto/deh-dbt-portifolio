"""OLTP mutation sidecar.

Runs as a Docker Compose service alongside the API, continuously simulating
realistic OLTP activity across all three domains.

Configuration via environment variables:
  MUTATE_INTERVAL   seconds between mutation cycles (default: 10)
  MUTATE_DOMAINS    comma-separated list of active domains (default: varejo,biblioteca,rede_social)
"""

import asyncio
import logging
import os
import random

import psycopg

log = logging.getLogger("mutator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [mutator] %(message)s")

_DSN = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ.get('POSTGRES_PORT', '5432')}"
    f"/{os.environ['POSTGRES_DB']}"
)
_INTERVAL = int(os.environ.get("MUTATE_INTERVAL", "10"))
_DOMAINS = os.environ.get("MUTATE_DOMAINS", "varejo,biblioteca,rede_social").split(",")

VALID_ESTADOS   = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE"]
VALID_SEGMENTOS = ["Ouro", "Prata", "Bronze"]
VALID_STATUSES  = ["pago", "cancelado", "devolvido"]


# ── Varejo mutations ──────────────────────────────────────────────────────────

def _varejo_insert_venda(cur):
    cur.execute("SELECT cliente_id FROM varejo.origem_cliente ORDER BY random() LIMIT 1")
    c = cur.fetchone()
    cur.execute("SELECT produto_id FROM varejo.origem_produto ORDER BY random() LIMIT 1")
    p = cur.fetchone()
    if not c or not p:
        return
    amount = round(random.uniform(50, 3500), 2)
    cur.execute(
        """
        INSERT INTO varejo.origem_venda
            (data_venda, produto_id, cliente_id, quantidade, valor_total, status)
        VALUES (current_date, %s, %s, %s, %s, 'pago')
        RETURNING venda_id
        """,
        (p[0], c[0], random.randint(1, 3), amount),
    )
    vid = cur.fetchone()[0]
    log.info("varejo  | venda %s criada (cliente=%s valor=%.2f)", vid, c[0], amount)


def _varejo_update_status(cur):
    cur.execute(
        "SELECT venda_id, status FROM varejo.origem_venda ORDER BY random() LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return
    new_s = random.choice([s for s in VALID_STATUSES if s != row[1]])
    cur.execute(
        "UPDATE varejo.origem_venda SET status=%s, updated_at=now() WHERE venda_id=%s",
        (new_s, row[0]),
    )
    log.info("varejo  | venda %s status %s → %s", row[0], row[1], new_s)


def _varejo_update_segmento(cur):
    cur.execute(
        "SELECT cliente_id, segmento FROM varejo.origem_cliente ORDER BY random() LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return
    new_seg = random.choice([s for s in VALID_SEGMENTOS if s != row[1]])
    cur.execute(
        "UPDATE varejo.origem_cliente SET segmento=%s, updated_at=now() WHERE cliente_id=%s",
        (new_seg, row[0]),
    )
    log.info("varejo  | cliente %s segmento %s → %s", row[0], row[1], new_seg)


# ── Biblioteca mutations ──────────────────────────────────────────────────────

def _biblioteca_insert_emprestimo(cur):
    cur.execute("SELECT usuario_id FROM biblioteca.usuario ORDER BY random() LIMIT 1")
    uid = cur.fetchone()
    cur.execute(
        "SELECT livro_id FROM biblioteca.livro WHERE quantidade_disponivel > 0 ORDER BY random() LIMIT 1"
    )
    lid = cur.fetchone()
    if not uid or not lid:
        return
    cur.execute(
        """
        INSERT INTO biblioteca.emprestimo
            (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista)
        VALUES (%s, %s, current_date, current_date + 14)
        RETURNING emprestimo_id
        """,
        (uid[0], lid[0]),
    )
    eid = cur.fetchone()[0]
    cur.execute(
        "UPDATE biblioteca.livro SET quantidade_disponivel=quantidade_disponivel-1 WHERE livro_id=%s",
        (lid[0],),
    )
    log.info("bib     | empréstimo %s criado (usuario=%s livro=%s)", eid, uid[0], lid[0])


def _biblioteca_return_livro(cur):
    cur.execute(
        """
        SELECT emprestimo_id, livro_id
        FROM biblioteca.emprestimo
        WHERE data_devolucao_real IS NULL
        ORDER BY random() LIMIT 1
        """
    )
    row = cur.fetchone()
    if not row:
        return
    cur.execute(
        "UPDATE biblioteca.emprestimo SET data_devolucao_real=current_date, updated_at=now() WHERE emprestimo_id=%s",
        (row[0],),
    )
    cur.execute(
        "UPDATE biblioteca.livro SET quantidade_disponivel=quantidade_disponivel+1 WHERE livro_id=%s",
        (row[1],),
    )
    log.info("bib     | empréstimo %s devolvido (livro=%s)", row[0], row[1])


# ── Rede Social mutations ─────────────────────────────────────────────────────

def _rede_insert_leitura(cur):
    cur.execute("SELECT pessoa_id FROM rede_social.pessoa ORDER BY random() LIMIT 1")
    pid = cur.fetchone()
    if not pid:
        return
    cur.execute(
        """
        SELECT livro_id FROM rede_social.livro
        WHERE livro_id NOT IN (
            SELECT livro_id FROM rede_social.leitura WHERE pessoa_id=%s
        )
        ORDER BY random() LIMIT 1
        """,
        (pid[0],),
    )
    lid = cur.fetchone()
    if not lid:
        return
    nota = round(random.uniform(2.0, 5.0), 1)
    cur.execute(
        "INSERT INTO rede_social.leitura (pessoa_id, livro_id, nota, data_leitura) VALUES (%s,%s,%s,current_date) ON CONFLICT DO NOTHING",
        (pid[0], lid[0], nota),
    )
    log.info("rede    | leitura pessoa=%s livro=%s nota=%.1f", pid[0], lid[0], nota)


def _rede_update_nota(cur):
    cur.execute(
        "SELECT pessoa_id, livro_id, nota FROM rede_social.leitura ORDER BY random() LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return
    new_nota = round(random.uniform(2.0, 5.0), 1)
    cur.execute(
        "UPDATE rede_social.leitura SET nota=%s, updated_at=now() WHERE pessoa_id=%s AND livro_id=%s",
        (new_nota, row[0], row[1]),
    )
    log.info("rede    | nota atualizada pessoa=%s livro=%s %.1f→%.1f", row[0], row[1], row[2], new_nota)


# ── Domain dispatch ───────────────────────────────────────────────────────────

_DOMAIN_MUTATIONS: dict[str, list] = {
    "varejo":      [_varejo_insert_venda, _varejo_update_status, _varejo_update_segmento],
    "biblioteca":  [_biblioteca_insert_emprestimo, _biblioteca_return_livro],
    "rede_social": [_rede_insert_leitura, _rede_update_nota],
}


def _run_cycle() -> None:
    domain = random.choice(_DOMAINS)
    mutations = _DOMAIN_MUTATIONS.get(domain, [])
    if not mutations:
        return
    fn = random.choice(mutations)
    with psycopg.connect(_DSN) as conn:
        with conn.cursor() as cur:
            fn(cur)
        conn.commit()


async def main() -> None:
    log.info("Mutator sidecar started — interval=%ds domains=%s", _INTERVAL, _DOMAINS)
    while True:
        try:
            _run_cycle()
        except Exception as exc:  # noqa: BLE001
            log.warning("Mutation skipped: %s", exc)
        await asyncio.sleep(_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
