from __future__ import annotations

from pydantic import BaseModel


class AboutResponse(BaseModel):
    models: list[dict]
    pipeline: list[str]
    training_data: list[dict]


class PrivacyResponse(BaseModel):
    retention_days: int
    training_requires_consent: bool
    encryption_at_rest: str
    encryption_in_transit: str
