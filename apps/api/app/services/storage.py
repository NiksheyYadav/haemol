from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlencode

from itsdangerous import URLSafeTimedSerializer

from app.core.config import settings
from app.utils.storage import delete_file, get_signed_url, read_file, upload_file

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.root = Path(settings.storage_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.serializer = URLSafeTimedSerializer(settings.secret_key, salt="biomarkly-storage")

    def save_bytes(self, folder: str, file_name: str, data: bytes, content_type: str | None = None) -> str:
        if settings.s3_bucket_name:
            return upload_file(folder, file_name, data, content_type)
        target = self.root / folder
        target.mkdir(parents=True, exist_ok=True)
        path = target / file_name
        try:
            path.write_bytes(data)
        except OSError as exc:
            logger.exception("Local storage write failed for %s", path)
            raise RuntimeError("Local storage write failed") from exc
        return str(path)

    def delete(self, storage_url: str | None) -> None:
        if not storage_url:
            return
        if storage_url.startswith("s3://"):
            delete_file(storage_url)
            return
        path = Path(storage_url)
        if path.exists():
            path.unlink()

    def read_bytes(self, storage_url: str) -> bytes:
        if storage_url.startswith("s3://"):
            return read_file(storage_url)
        return Path(storage_url).read_bytes()

    def signed_url(self, storage_url: str) -> str:
        if storage_url.startswith("s3://"):
            return get_signed_url(storage_url, expires_in=settings.signed_url_ttl_seconds)
        token = self.serializer.dumps({"path": storage_url})
        return f"/internal/files?{urlencode({'token': token})}"

    def resolve_signed_token(self, token: str) -> Path:
        payload = self.serializer.loads(token, max_age=settings.signed_url_ttl_seconds)
        return Path(payload["path"])


storage_service = StorageService()
