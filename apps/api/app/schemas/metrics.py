from __future__ import annotations

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    extraction_success_rate: float
    avg_analysis_latency: float
    error_rate_by_type: dict[str, float]
    audio_usage_by_language: dict[str, int]
    feedback_score_7d: float
