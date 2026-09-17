"""dlt source definitions — REST API extraction for all OLTP domains."""
import dlt
from dlt.sources.rest_api import rest_api_source

_PAGE_SIZE = 1_000

DOMAINS: dict[str, list[str]] = {
    "varejo": ["clientes", "produtos", "vendas"],
    "biblioteca": ["usuarios", "livros", "emprestimos", "autores", "multas"],
    "rede_social": ["pessoas", "leituras", "conexoes", "generos", "livros"],
}


def oltp_source(domain: str, base_url: str) -> dlt.sources.DltSource:
    """Build a dlt REST API source for the given OLTP domain."""
    return rest_api_source(
        {
            "client": {"base_url": base_url},
            "resources": [
                {
                    "name": entity,
                    "endpoint": {
                        "path": f"/{domain}/{entity}",
                        "paginator": {
                            "type": "offset",
                            "limit": _PAGE_SIZE,
                            "offset_param": "offset",
                            "limit_param": "limit",
                            "stop_after_empty_page": True,
                        },
                    },
                    "write_disposition": "replace",
                }
                for entity in DOMAINS[domain]
            ],
        },
        name=domain,
    )
