from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import EventLog

try:
    import posthog
except ImportError:  # pragma: no cover
    posthog = None


def capture_event(db: Session, name: str, payload: dict, report_id: str | None = None, analysis_id: str | None = None) -> None:
    event = EventLog(name=name, payload=payload, report_id=report_id, analysis_id=analysis_id)
    db.add(event)
    db.commit()
    if settings.posthog_api_key and posthog is not None:
        posthog.api_key = settings.posthog_api_key
        posthog.host = settings.posthog_host
        distinct_id = report_id or analysis_id or "anonymous"
        posthog.capture(distinct_id=distinct_id, event=name, properties=payload)
