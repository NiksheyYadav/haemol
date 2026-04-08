from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import EventCreate
from app.services.telemetry import capture_event

router = APIRouter(tags=["events"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> dict:
    capture_event(db, payload.name, payload.payload, payload.report_id, payload.analysis_id)
    return {"accepted": True}
