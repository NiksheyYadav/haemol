from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Analysis, AudioJob, Feedback
from app.db.session import get_db
from app.schemas.analysis import AnalysisResponse, AudioRequest, FeedbackRequest
from app.services.analysis_service import build_detailed_report
from app.services.storage import storage_service
from app.services.telemetry import capture_event
from app.tasks.jobs import generate_audio

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _run_task(task, *args):
    if settings.task_mode == "async":
        return task.delay(*args).id
    return task(*args)


def _serialize_analysis(analysis: Analysis) -> AnalysisResponse:
    detailed_report = build_detailed_report(
        analysis.summary,
        analysis.conditions,
        analysis.abnormal_params,
        analysis.specialist_models,
        analysis.confidence_scores,
    )
    return AnalysisResponse(
        id=analysis.id,
        report_id=analysis.report_id,
        status=analysis.status,
        created_at=analysis.created_at,
        summary=analysis.summary,
        conditions=analysis.conditions,
        abnormal_params=analysis.abnormal_params,
        specialist_models=analysis.specialist_models,
        recommendations=analysis.recommendations,
        confidence_scores=analysis.confidence_scores,
        detailed_report=detailed_report,
        audio_jobs=[
            {
                "id": job.id,
                "language": job.language,
                "status": job.status,
                "audio_url": storage_service.signed_url(job.audio_url) if job.audio_url else None,
                "fallback_text": job.fallback_text,
                "created_at": job.created_at,
            }
            for job in analysis.audio_jobs
        ],
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisResponse:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _serialize_analysis(analysis)


@router.post("/{analysis_id}/audio")
def request_audio(analysis_id: str, payload: AudioRequest, db: Session = Depends(get_db)) -> dict:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    existing_job = (
        db.query(AudioJob)
        .filter(AudioJob.analysis_id == analysis_id, AudioJob.language == payload.language)
        .order_by(AudioJob.created_at.desc())
        .first()
    )
    if existing_job is not None and existing_job.status in {"pending", "done"}:
        return {"analysis_id": analysis_id, "audio_job_id": existing_job.id, "language": payload.language}
    job_id = _run_task(generate_audio, analysis_id, payload.language)
    capture_event(db, "audio_played", {"language": payload.language}, analysis_id=analysis_id)
    return {"analysis_id": analysis_id, "audio_job_id": job_id, "language": payload.language}


@router.get("/{analysis_id}/audio/{lang}")
def get_audio_status(analysis_id: str, lang: str, db: Session = Depends(get_db)) -> dict:
    job = (
        db.query(AudioJob)
        .filter(AudioJob.analysis_id == analysis_id, AudioJob.language == lang)
        .order_by(AudioJob.created_at.desc())
        .first()
    )
    if job is None:
        return {"status": "pending", "audio_url": None, "fallback_text": None}
    return {
        "status": job.status,
        "audio_url": storage_service.signed_url(job.audio_url) if job.audio_url else None,
        "fallback_text": job.fallback_text,
    }


@router.post("/{analysis_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(analysis_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)) -> dict:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    feedback = Feedback(analysis_id=analysis_id, sentiment=payload.sentiment, text=payload.text)
    db.add(feedback)
    db.commit()
    capture_event(db, "feedback_submitted", {"sentiment": payload.sentiment, "has_text": bool(payload.text)}, analysis_id=analysis_id)
    return {"ok": True}
