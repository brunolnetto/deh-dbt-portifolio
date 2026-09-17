import os

OLTP_API_URL: str = os.getenv("OLTP_API_URL", "http://localhost:8001")
RUSTFS_ENDPOINT: str = os.getenv("RUSTFS_ENDPOINT", "localhost:9000")
RUSTFS_ACCESS_KEY: str = os.getenv("RUSTFS_ACCESS_KEY", "minioadmin")
RUSTFS_SECRET_KEY: str = os.getenv("RUSTFS_SECRET_KEY", "minioadmin")
LANDING_BUCKET: str = os.getenv("LANDING_BUCKET", "landing")
EXTRACT_INTERVAL: int = int(os.getenv("EXTRACT_INTERVAL", "30"))

# PostgreSQL landing schema target
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5437"))
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "dbt")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "dbt")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "portifolio")
POSTGRES_DSN: str = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
