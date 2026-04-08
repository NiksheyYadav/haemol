from __future__ import annotations

import pytest

from app.core.config import Settings


def test_production_rejects_localhost_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/biomarkly")

    with pytest.raises(ValueError, match="DATABASE_URL cannot point to localhost in production"):
        Settings()


def test_production_allows_remote_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@biomarkly-db.internal:5432/biomarkly")

    settings = Settings()

    assert settings.database_url.endswith("/biomarkly")
