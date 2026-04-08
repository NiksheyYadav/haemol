from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    task_mode: str = "sync"
    app_name: str = "Biomarkly API"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./biomarkly.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "ap-south-1"
    aws_endpoint_url: str | None = None
    s3_bucket_name: str | None = None
    sarvam_api_key: str | None = None
    posthog_api_key: str | None = None
    posthog_host: str = "https://app.posthog.com"
    admin_metrics_token: str = "change-me"
    report_retention_days: int = 30
    upload_max_mb: int = 10
    upload_max_chars: int = 50000
    rate_limit_per_hour: int = 10
    signed_url_ttl_seconds: int = 900
    storage_root: Path = Field(default_factory=lambda: Path("apps/api/storage"))
    spacy_model: str = "en_core_web_sm"


settings = Settings()
