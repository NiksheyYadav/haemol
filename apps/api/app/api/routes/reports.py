from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import enforce_hourly_limit
from app.db.models import Analysis, AuditLog, ExtractedParam, Report
from app.db.session import get_db
from app.schemas.report import ReportCreateRequest, ReportPatchRequest, ReportResponse
from app.services.reference_data import reference_range_for
from app.services.storage import storage_service
from app.services.telemetry import capture_event
from app.tasks.jobs import run_analysis, run_extraction

router = APIRouter(prefix="/reports", tags=["reports"])


def _run_task(task, *args):
    if settings.task_mode == "async":
        return task.delay(*args).id
    return task(*args)


def _serialize_param(item: ExtractedParam) -> dict:
    return {
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


def _serialize_report(report: Report) -> ReportResponse:
    latest_analysis = report.analyses[-1].id if report.analyses else None
    return ReportResponse(
        id=report.id,
        source_type=report.source_type,
        locale=report.locale,
        sex=report.sex,
        age=report.age,
        status=report.status,
        extraction_status=report.extraction_status,
        extraction_step=report.extraction_step,
        created_at=report.created_at,
        file_name=report.file_name,
        raw_text=report.raw_text,
        extracted_params=[_serialize_param(item) for item in report.extracted_params],
        analysis_id=latest_analysis,
        error_message=report.error_message,
    )


@router.post("", response_model=ReportResponse, dependencies=[Depends(enforce_hourly_limit)])
async def create_report(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(default=None),
    locale: str = Form("en"),
    sex: str = Form("other"),
    age: int = Form(0),
    consent_given: bool = Form(False),
) -> ReportResponse:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        if file is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")
        data = await file.read()
        if len(data) > settings.upload_max_mb * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")
        try:
            storage_url = storage_service.save_bytes("reports", file.filename or "report.bin", data, file.content_type)
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        report = Report(
            source_type="file",
            locale=locale,
            sex=sex,
            age=age,
            file_name=file.filename,
            file_url=storage_url,
            consent_given=consent_given,
            status="pending",
            extraction_status="pending",
            extraction_step="queued",
        )
    else:
        body = ReportCreateRequest.model_validate(await request.json())
        if body.raw_text and len(body.raw_text) > settings.upload_max_chars:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Text exceeds 50k characters")
        report = Report(
            source_type=body.source_type,
            locale=body.locale,
            sex=body.sex,
            age=body.age,
            raw_text=body.raw_text or json.dumps(body.manual_params or {}),
            consent_given=body.consent_given,
            status="pending",
            extraction_status="pending",
            extraction_step="queued",
        )
    db.add(report)
    db.commit()
    db.refresh(report)
    db.add(AuditLog(entity_id=report.id, entity_type="Report", event="created", detail={"source_type": report.source_type}))
    db.commit()
    capture_event(db, "upload_started", {"source_type": report.source_type}, report_id=report.id)
    _run_task(run_extraction, report.id)
    db.refresh(report)
    return _serialize_report(report)


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)) -> ReportResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _serialize_report(report)


@router.patch("/{report_id}", response_model=ReportResponse)
def patch_report(report_id: str, payload: ReportPatchRequest, db: Session = Depends(get_db)) -> ReportResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    db.query(ExtractedParam).filter(ExtractedParam.report_id == report_id).delete()
    for item in payload.extracted_params:
        value = float(item["value"])
        low, high, unit, category = reference_range_for(item["canonical_name"], report.sex, report.age)
        delta = None
        flagged = False
        if low is not None and value < low:
            delta = round(value - low, 2)
            flagged = True
        elif high is not None and value > high:
            delta = round(value - high, 2)
            flagged = True
        db.add(
            ExtractedParam(
                report_id=report.id,
                name=item["name"],
                canonical_name=item["canonical_name"],
                value=value,
                unit=item.get("unit", "") or unit,
                confidence=float(item.get("confidence", 0.5)),
                is_flagged=flagged,
                ref_range_key=item.get("ref_range_key", f"{item['canonical_name']}:{category.lower()}"),
                category=item.get("category", category),
                raw_reference_range=item.get("raw_reference_range", f"{low}–{high} {unit}".strip()),
                range_min=low,
                range_max=high,
                delta_from_range=delta,
                note=item.get("note"),
            )
        )
    db.query(Analysis).filter(Analysis.report_id == report.id).delete()
    db.add(AuditLog(entity_id=report.id, entity_type="Report", event="params_edited", detail={"count": len(payload.extracted_params)}))
    db.commit()
    db.refresh(report)
    return _serialize_report(report)


@router.post("/{report_id}/analyze")
def analyze_report(report_id: str, db: Session = Depends(get_db)) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not report.extracted_params:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No extracted params available")
    analysis_id = _run_task(run_analysis, report.id)
    capture_event(db, "analysis_done", {"report_id": report_id}, report_id=report_id)
    return {"report_id": report_id, "analysis_id": analysis_id}


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: str, db: Session = Depends(get_db)) -> None:
    report = db.get(Report, report_id)
    if report is None:
        return None
    storage_service.delete(report.file_url)
    db.delete(report)
    db.commit()
