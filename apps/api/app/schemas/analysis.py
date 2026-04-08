from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import (
    AnalysisConditionModel,
    AudioJobModel,
    ExtractedParamModel,
    RecommendationItemModel,
    SpecialistModelResultModel,
)


class AnalysisResponse(BaseModel):
    id: str
    report_id: str
    status: str
    created_at: datetime
    summary: str
    conditions: list[AnalysisConditionModel]
    abnormal_params: list[ExtractedParamModel]
    specialist_models: list[SpecialistModelResultModel]
    recommendations: list[RecommendationItemModel]
    confidence_scores: dict[str, float]
    detailed_report: dict
    audio_jobs: list[AudioJobModel] = Field(default_factory=list)


class AudioRequest(BaseModel):
    language: str


class FeedbackRequest(BaseModel):
    sentiment: str = Field(pattern=r"^(up|down)$")
    text: str | None = Field(default=None, max_length=200)
