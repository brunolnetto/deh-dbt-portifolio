import os

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

POSTGRES_DSN = "postgresql://{user}:{password}@{host}:{port}/{db}".format(
    user=os.getenv("POSTGRES_USER", "dbt"),
    password=os.getenv("POSTGRES_PASSWORD", "dbt"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5437"),
    db=os.getenv("POSTGRES_DB", "portifolio"),
)

SODA_CONFIG = os.path.join(os.path.dirname(__file__), "../soda/configuration.yml")
SODA_CHECKS_DIR = os.path.join(os.path.dirname(__file__), "../soda/checks")


@pytest.fixture(scope="session")
def pg_conn():
    with psycopg.connect(POSTGRES_DSN) as conn:
        yield conn
