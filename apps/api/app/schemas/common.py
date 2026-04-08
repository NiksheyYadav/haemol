from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReferenceRangeModel(BaseModel):
    min: float | None
    max: float | None
    unit: str
    note: str | None = None


class ExtractedParamModel(BaseModel):
    id: str
    name: str
    canonical_name: str
    category: str
    value: float
    unit: str
    confidence: float
    is_flagged: bool
    ref_range_key: str
    raw_reference_range: str
    reference_range: ReferenceRangeModel
    delta_from_range: float | None = None
    note: str | None = None


class AnalysisConditionModel(BaseModel):
    condition: str
    severity: str
    summary: str
    explanation: str
    probability: float
    model_name: str
    model_version: str


class SpecialistModelResultModel(BaseModel):
    model_name: str
    model_version: str
    probability: float
    severity: str
    condition: str
    explanation: str
    top_features: list[str]


class RecommendationLinkModel(BaseModel):
    label: str
    href: str


class RecommendationItemModel(BaseModel):
    text: str
    caveat: str
    sources: list[RecommendationLinkModel]


class AudioJobModel(BaseModel):
    id: str
    language: str
    status: str
    audio_url: str | None = None
    fallback_text: str | None = None
    created_at: datetime


class EventCreate(BaseModel):
    name: str = Field(pattern=r"^[a-z_]+$")
    report_id: str | None = None
    analysis_id: str | None = None
    payload: dict = Field(default_factory=dict)
