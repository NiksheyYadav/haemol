from __future__ import annotations

import mimetypes
import secrets
from urllib.parse import urlparse, urlunparse

try:
    import boto3
    from botocore.client import BaseClient
    from botocore.config import Config
except ImportError:  # pragma: no cover
    boto3 = None
    BaseClient = object  # type: ignore[assignment,misc]
    Config = None  # type: ignore[assignment]

from app.core.config import settings


def _make_client() -> BaseClient | None:
    if not settings.s3_bucket_name or boto3 is None or Config is None:
        return None
    session = boto3.session.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    return session.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url or None,
        config=Config(signature_version="s3v4"),
    )


def _bucket() -> str | None:
    return settings.s3_bucket_name


def _object_url(key: str) -> str:
    bucket = _bucket()
    if not bucket:
        raise RuntimeError("S3 bucket is not configured")
    return f"s3://{bucket}/{key}"


def _parse_s3_url(storage_url: str) -> tuple[str, str]:
    parsed = urlparse(storage_url)
    if parsed.scheme != "s3":
        raise ValueError(f"Unsupported S3 URL: {storage_url}")
    return parsed.netloc, parsed.path.lstrip("/")


def upload_file(folder: str, file_name: str, data: bytes, content_type: str | None = None) -> str:
    bucket = _bucket()
    client = _make_client()
    if not bucket or client is None:
        raise RuntimeError("S3 is not configured")
    safe_name = f"{secrets.token_hex(8)}-{file_name}"
    key = f"{folder}/{safe_name}"
    resolved_content_type = content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    put_kwargs = {
        "Bucket": bucket,
        "Key": key,
        "Body": data,
        "ContentType": resolved_content_type,
    }
    if resolved_content_type.startswith("audio/"):
        put_kwargs["ContentDisposition"] = "inline"
    client.put_object(**put_kwargs)
    return _object_url(key)


def get_signed_url(storage_url: str, expires_in: int = 900) -> str:
    client = _make_client()
    if client is None:
        raise RuntimeError("S3 is not configured")
    bucket, key = _parse_s3_url(storage_url)
    guessed_content_type = mimetypes.guess_type(key)[0]
    params = {"Bucket": bucket, "Key": key}
    if guessed_content_type and guessed_content_type.startswith("audio/"):
        params["ResponseContentType"] = guessed_content_type
        params["ResponseContentDisposition"] = "inline"
    url = client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )
    if settings.aws_endpoint_url and "localstack" in settings.aws_endpoint_url:
        parsed = urlparse(url)
        return urlunparse(parsed._replace(netloc="localhost:4566"))
    return url


def delete_file(storage_url: str) -> None:
    client = _make_client()
    if client is None:
        raise RuntimeError("S3 is not configured")
    bucket, key = _parse_s3_url(storage_url)
    client.delete_object(Bucket=bucket, Key=key)


def read_file(storage_url: str) -> bytes:
    client = _make_client()
    if client is None:
        raise RuntimeError("S3 is not configured")
    bucket, key = _parse_s3_url(storage_url)
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()
