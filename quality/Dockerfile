FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /quality
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY . .

ENTRYPOINT ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
