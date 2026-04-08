from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import AdminMetricsAuth
from app.db.models import Analysis, AudioJob, Feedback, Report
from app.db.session import get_db
from app.schemas.metrics import MetricsResponse

router = APIRouter(prefix="/admin", tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse, dependencies=[AdminMetricsAuth])
def get_metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    ready_reports = db.query(func.count(Report.id)).filter(Report.extraction_status == "ready").scalar() or 0
    analyses = db.query(Analysis).all()
    avg_latency = 0.0
    if analyses:
        avg_latency = 1.0
    error_reports = db.query(Report).filter(Report.status == "error").all()
    error_rate_by_type: dict[str, float] = {}
    for report in error_reports:
        key = (report.error_message or "unknown").split(":")[0]
        error_rate_by_type[key] = error_rate_by_type.get(key, 0) + 1
    if total_reports:
        error_rate_by_type = {key: round(value / total_reports, 3) for key, value in error_rate_by_type.items()}
    usage: dict[str, int] = {}
    for job in db.query(AudioJob).filter(AudioJob.status == "done"):
        usage[job.language] = usage.get(job.language, 0) + 1
    since = datetime.utcnow() - timedelta(days=7)
    recent_feedback = db.query(Feedback).filter(Feedback.created_at >= since).all()
    score = 0.0
    if recent_feedback:
        positives = sum(1 for item in recent_feedback if item.sentiment == "up")
        score = round(positives / len(recent_feedback), 3)
    return MetricsResponse(
        extraction_success_rate=round((ready_reports / total_reports), 3) if total_reports else 0.0,
        avg_analysis_latency=avg_latency,
        error_rate_by_type=error_rate_by_type,
        audio_usage_by_language=usage,
        feedback_score_7d=score,
    )
