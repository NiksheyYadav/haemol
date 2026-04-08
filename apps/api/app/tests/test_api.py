from __future__ import annotations

import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ADMIN_METRICS_TOKEN"] = "test-token"
os.environ["SARVAM_API_KEY"] = ""
os.environ["S3_BUCKET_NAME"] = ""
os.environ["REDIS_URL"] = "redis://127.0.0.1:6399/99"

from fastapi.testclient import TestClient

from app.main import app
from app.core.rate_limit import limiter


client = TestClient(app)


def setup_function() -> None:
    limiter._memory.clear()


def test_report_text_flow() -> None:
    response = client.post(
        "/reports",
        json={
            "source_type": "text",
            "locale": "en",
            "sex": "male",
            "age": 42,
            "consent_given": True,
            "raw_text": "Hemoglobin: 10.2 g/dL\nGlucose: 128 mg/dL\nCreatinine: 1.9 mg/dL\nTSH: 5.5",
        },
    )
    assert response.status_code == 200
    report = response.json()
    assert report["id"]
    assert report["extracted_params"]


def test_analysis_returns_detailed_report_and_audio_fallback() -> None:
    report_response = client.post(
        "/reports",
        json={
            "source_type": "text",
            "locale": "en",
            "sex": "male",
            "age": 42,
            "consent_given": True,
            "raw_text": "Hemoglobin: 10.2 g/dL\nGlucose: 128 mg/dL\nCreatinine: 1.9 mg/dL\nTSH: 5.5",
        },
    )
    assert report_response.status_code == 200
    report_id = report_response.json()["id"]

    analysis_response = client.post(f"/reports/{report_id}/analyze")
    assert analysis_response.status_code == 200
    analysis_id = analysis_response.json()["analysis_id"]

    get_analysis_response = client.get(f"/analyses/{analysis_id}")
    assert get_analysis_response.status_code == 200
    analysis = get_analysis_response.json()
    assert analysis["detailed_report"]["overview"]
    assert analysis["detailed_report"]["key_findings"]
    assert analysis["detailed_report"]["parameter_findings"]
    assert any("anemia" in item.lower() or "hemoglobin" in item.lower() for item in analysis["detailed_report"]["key_findings"])
    assert any(
        item["parameter_name"].lower() == "hemoglobin" and "carrying less oxygen" in item["explanation"].lower()
        for item in analysis["detailed_report"]["parameter_findings"]
    )
    assert any("iron levels" in item["clinical_note"].lower() for item in analysis["detailed_report"]["parameter_findings"])

    audio_response = client.post(f"/analyses/{analysis_id}/audio", json={"language": "english"})
    assert audio_response.status_code == 200

    audio_status_response = client.get(f"/analyses/{analysis_id}/audio/english")
    assert audio_status_response.status_code == 200
    audio_status = audio_status_response.json()
    assert audio_status["status"] in {"done", "failed"}
    assert audio_status["fallback_text"]


def test_metrics_requires_bearer() -> None:
    response = client.get("/admin/metrics")
    assert response.status_code == 401
    ok = client.get("/admin/metrics", headers={"Authorization": "Bearer test-token"})
    assert ok.status_code == 200
