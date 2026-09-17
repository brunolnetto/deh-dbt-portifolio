"""S3-compatible writer for RustFS landing zone using Parquet format."""
import io
import logging
from datetime import datetime, timezone
from typing import Any

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError

from .config import LANDING_BUCKET, RUSTFS_ACCESS_KEY, RUSTFS_ENDPOINT, RUSTFS_SECRET_KEY

log = logging.getLogger(__name__)

_s3: Any = None


def _get_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{RUSTFS_ENDPOINT}",
            aws_access_key_id=RUSTFS_ACCESS_KEY,
            aws_secret_access_key=RUSTFS_SECRET_KEY,
            region_name="us-east-1",
        )
    return _s3


def _ensure_bucket() -> None:
    client = _get_client()
    try:
        client.head_bucket(Bucket=LANDING_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=LANDING_BUCKET)
        log.info("Created bucket: %s", LANDING_BUCKET)


def write_parquet(records: list[dict], s3_path: str) -> int:
    """Write records as a Parquet file to RustFS at s3://{BUCKET}/{s3_path}/{timestamp}.parquet.

    Returns number of records written (0 if records is empty).
    """
    if not records:
        log.debug("[%s] No records — skipping write.", s3_path)
        return 0

    _ensure_bucket()

    table = pa.Table.from_pylist(records)
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"{s3_path}/{ts}.parquet"

    _get_client().put_object(Bucket=LANDING_BUCKET, Key=key, Body=buf.getvalue())
    log.info("[%s] Wrote %d records → s3://%s/%s", s3_path, len(records), LANDING_BUCKET, key)
    return len(records)
