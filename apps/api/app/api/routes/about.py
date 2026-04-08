from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.models.base_predictor import get_model_metadata
from app.schemas.about import AboutResponse, PrivacyResponse

router = APIRouter(tags=["about"])


@router.get("/about", response_model=AboutResponse)
def get_about() -> AboutResponse:
    def _model_entry(key: str, display_name: str, fallback_f1: float) -> dict:
        metadata = get_model_metadata(key)
        metrics = metadata.get("metrics", {}) if metadata else {}
        f1 = metrics.get("f1", None)
        version = metadata.get("version", "2026.03") if metadata else "2026.03"
        f1_percent = round(f1 * 100, 1) if f1 is not None else fallback_f1
        return {"name": display_name, "f1": f1_percent, "version": version}

    return AboutResponse(
        models=[
            _model_entry("anemia", "Anemia", 97.3),
            _model_entry("diabetes", "Diabetes", 93.9),
            _model_entry("kidney", "Kidney", 100.0),
            _model_entry("liver", "Liver", 71.1),
            _model_entry("thyroid", "Thyroid", 67.9),
        ],
        pipeline=["regex", "spaCy NER", "pdfplumber", "pytesseract"],
        training_data=[
            {"name": "Diabetes", "size": "100k"},
            {"name": "Liver", "size": "30k"},
            {"name": "Kidney", "size": "CKD dataset"},
            {"name": "Thyroid", "size": "9k rows"},
        ],
    )


@router.get("/about/privacy", response_model=PrivacyResponse)
def get_privacy() -> PrivacyResponse:
    return PrivacyResponse(
        retention_days=settings.report_retention_days,
        training_requires_consent=True,
        encryption_at_rest="AES-256",
        encryption_in_transit="TLS 1.2+",
    )
