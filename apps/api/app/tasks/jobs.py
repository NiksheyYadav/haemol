from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.models import Analysis, AudioJob, AuditLog, ExtractedParam, Report
from app.db.session import SessionLocal
from app.pipeline.extract import canonicalize, extract_params, normalize_text, ocr_image, parse_pdf
from app.services.analysis_service import build_detailed_report, run_specialist_models
from app.services.audio import audio_service
from app.services.reference_data import reference_range_for
from app.services.storage import storage_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _read_bytes(report: Report) -> bytes:
    if not report.file_url:
        return b""
    return storage_service.read_bytes(report.file_url)


@celery_app.task(name="run_extraction")
def run_extraction(report_id: str) -> str:
    db: Session = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if report is None:
            return report_id
        report.status = "processing"
        report.extraction_status = "processing"
        report.extraction_step = "parsing"
        db.commit()

        if report.source_type == "file" and report.file_url:
            file_bytes = _read_bytes(report)
            file_name = (report.file_name or "").lower()
            if file_name.endswith(".pdf"):
                raw_text = parse_pdf(file_bytes)
            elif file_name.endswith(".txt"):
                raw_text = file_bytes.decode("utf-8", errors="ignore")
            else:
                report.extraction_step = "ocr"
                db.commit()
                raw_text = ocr_image(file_bytes)
        elif report.source_type == "text":
            raw_text = report.raw_text or ""
        else:
            raw_text = report.raw_text or ""

        report.raw_text = normalize_text(raw_text)
        report.extraction_step = "nlp_extraction"
        db.commit()

        params = canonicalize(extract_params(report.raw_text))
        db.query(ExtractedParam).filter(ExtractedParam.report_id == report.id).delete()
        for param in params:
            low, high, _, _ = reference_range_for(param.canonical_name, report.sex, report.age)
            delta = None
            flagged = False
            if low is not None and param.value < low:
                delta = round(param.value - low, 2)
                flagged = True
            elif high is not None and param.value > high:
                delta = round(param.value - high, 2)
                flagged = True
            db.add(
                ExtractedParam(
                    report_id=report.id,
                    name=param.name,
                    canonical_name=param.canonical_name,
                    value=param.value,
                    unit=param.unit,
                    confidence=param.confidence,
                    is_flagged=flagged,
                    ref_range_key=param.ref_range_key,
                    category=param.category,
                    raw_reference_range=f"{low}–{high} {param.unit}".strip() if low is not None or high is not None else param.raw_reference_range,
                    range_min=low,
                    range_max=high,
                    delta_from_range=delta,
                    note=param.note,
                )
            )
        report.status = "ready"
        report.extraction_status = "ready"
        report.extraction_step = "done"
        db.add(AuditLog(entity_id=report.id, entity_type="Report", event="extraction_completed", detail={"count": len(params)}))
        db.commit()
        return report.id
    except Exception as exc:
        report = db.get(Report, report_id)
        if report is not None:
            report.status = "error"
            report.extraction_status = "error"
            report.extraction_step = "failed"
            report.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="run_analysis")
def run_analysis(report_id: str) -> str:
    db: Session = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if report is None:
            return report_id
        params = {item.canonical_name: item.value for item in report.extracted_params}
        specialist_models, conditions, recommendations, confidence_scores, summary = run_specialist_models(params, report.age, report.sex)
        abnormal_params = [
            {
                "id": item.id,
                "name": item.name,
                "canonical_name": item.canonical_name,
                "category": item.category,
                "value": item.value,
                "unit": item.unit,
                "confidence": item.confidence,
                "is_flagged": item.is_flagged,
                "ref_range_key": item.ref_range_key,
                "raw_reference_range": item.raw_reference_range,
                "reference_range": {"min": item.range_min, "max": item.range_max, "unit": item.unit, "note": item.note},
                "delta_from_range": item.delta_from_range,
                "note": item.note,
            }
            for item in report.extracted_params
            if item.is_flagged
        ]
        if not conditions and abnormal_params:
            summary = "Some extracted parameters were outside the reference range, but no strong specialist-model pattern was detected."
        detailed_report = build_detailed_report(summary, conditions, abnormal_params, specialist_models, confidence_scores)
        analysis = Analysis(
            report_id=report.id,
            model_name="ensemble",
            model_version="2026.03",
            status="done",
            summary=detailed_report["overview"],
            conditions=conditions,
            abnormal_params=abnormal_params,
            specialist_models=specialist_models,
            recommendations=recommendations,
            confidence_scores=confidence_scores,
        )
        db.add(analysis)
        db.flush()
        db.add(AuditLog(entity_id=report.id, entity_type="Report", event="analysis_completed", detail={"analysis_id": analysis.id}))
        db.commit()
        return analysis.id
    finally:
        db.close()


@celery_app.task(name="generate_audio")
def generate_audio(analysis_id: str, lang: str) -> str:
    db: Session = SessionLocal()
    try:
        analysis = db.get(Analysis, analysis_id)
        if analysis is None:
            return analysis_id
        payload = {
            "conditions": analysis.conditions,
            "summary": analysis.summary,
            "detailed_report": build_detailed_report(
                analysis.summary,
                analysis.conditions,
                analysis.abnormal_params,
                analysis.specialist_models,
                analysis.confidence_scores,
            ),
        }
        fallback_text = audio_service.summarize(payload, lang)
        job = AudioJob(analysis_id=analysis_id, language=lang, status="pending", fallback_text=fallback_text)
        try:
            audio_bytes, fallback_text = audio_service.generate(analysis_id, lang, payload)
            job.fallback_text = fallback_text
            if audio_bytes:
                storage_url = storage_service.save_bytes("audio", f"{analysis_id}-{lang}.mp3", audio_bytes, "audio/mpeg")
                job.audio_url = storage_url
                job.status = "done"
            else:
                job.status = "failed"
        except Exception:
            logger.exception("Audio generation failed for analysis %s in %s", analysis_id, lang)
            job.status = "failed"
        db.add(job)
        db.add(AuditLog(entity_id=analysis_id, entity_type="Analysis", event="audio_generated", detail={"language": lang, "status": job.status}))
        db.commit()
        return job.id
    finally:
        db.close()
