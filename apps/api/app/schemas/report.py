from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ExtractedParamModel


class ReportCreateRequest(BaseModel):
    source_type: str
    locale: str = "en"
    sex: str
    age: int = Field(ge=0, le=120)
    consent_given: bool = False
    raw_text: str | None = None
    manual_params: dict[str, float] | None = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in {"text", "manual"}:
            raise ValueError("source_type must be text or manual for JSON requests")
        return value


class ReportPatchRequest(BaseModel):
    extracted_params: list[dict]


class ReportResponse(BaseModel):
    id: str
    source_type: str
    locale: str
    sex: str
    age: int
    status: str
    extraction_status: str
    extraction_step: str
    created_at: datetime
    file_name: str | None = None
    raw_text: str | None = None
    extracted_params: list[ExtractedParamModel]
    analysis_id: str | None = None
    error_message: str | None = None
