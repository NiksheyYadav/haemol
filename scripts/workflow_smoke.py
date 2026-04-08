"""End-to-end smoke test for Biomarkly API.

This script:
1) Creates a text report using sample lab text
2) Polls the report until extraction completes
3) Triggers analysis if needed
4) Polls analysis until results are ready

Usage:
    python scripts/workflow_smoke.py

Env vars:
    API_URL: base URL of the API (default http://localhost:8000)
    TIMEOUT: total timeout seconds (default 240)
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, Tuple

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = int(os.getenv("TIMEOUT", "240"))
POLL_INTERVAL = 2.0

SAMPLE_TEXT = """Scanned Document - Page 1
HOSPITAL LAB
WBC: 11,000 /mcL  (High)
RBC: 4.5 mil
Hb : 12.1 g/dL
Hct : 36 %
Platelets : 180,000
MCV : 80 fL
MCH : 27 pg
MCHC : 33 g/dL
Glucose (Random): 110 mg/dL
Note: Patient showed symptoms of fever.
"""


def _req(method: str, path: str, **kwargs: Any) -> requests.Response:
    url = f"{API_URL}{path}"
    resp = requests.request(method, url, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp


def create_report() -> Dict[str, Any]:
    payload = {
        "source_type": "text",
        "locale": "en",
        "sex": "male",
        "age": 30,
        "consent_given": True,
        "raw_text": SAMPLE_TEXT,
    }
    resp = _req("POST", "/reports", json=payload)
    return resp.json()


def poll_report(report_id: str) -> Tuple[Dict[str, Any], bool]:
    start = time.time()
    while True:
        resp = _req("GET", f"/reports/{report_id}")
        data = resp.json()
        step = data.get("extraction_step")
        elapsed = time.time() - start
        print(f"[report] step={step} error={data.get('error_message')} analysis_id={data.get('analysis_id')} elapsed={int(elapsed)}s")
        if step == "done":
            return data, True
        if elapsed > TIMEOUT:
            print("Extraction timed out before reaching 'done'")
            return data, False
        time.sleep(POLL_INTERVAL)


def analyze(report_id: str) -> str:
    resp = _req("POST", f"/reports/{report_id}/analyze")
    return resp.json().get("analysis_id")  # celery task id (not the DB analysis id)


def poll_report_for_analysis(report_id: str) -> Tuple[str | None, Dict[str, Any]]:
    start = time.time()
    while True:
        resp = _req("GET", f"/reports/{report_id}")
        data = resp.json()
        analysis_id = data.get("analysis_id")
        elapsed = int(time.time() - start)
        print(f"[report] waiting for analysis_id={analysis_id} elapsed={elapsed}s")
        if analysis_id:
            return analysis_id, data
        if elapsed > TIMEOUT:
            return None, data
        time.sleep(POLL_INTERVAL)


def poll_analysis(analysis_id: str) -> Dict[str, Any]:
    start = time.time()
    while True:
        resp = _req("GET", f"/analyses/{analysis_id}")
        data = resp.json()
        status = data.get("status")
        print(f"[analysis] status={status} conditions={len(data.get('conditions', []))}")
        if status == "done" or (time.time() - start) > TIMEOUT:
            return data
        time.sleep(POLL_INTERVAL)


def main() -> None:
    print(f"Using API_URL={API_URL}")
    try:
        report = create_report()
    except Exception as exc:  # pragma: no cover - smoke helper
        print(f"Failed to create report: {exc}")
        sys.exit(1)

    report_id = report.get("id")
    if not report_id:
        print("Report creation did not return an id")
        sys.exit(1)

    print(f"Created report: {report_id}")
    report, done = poll_report(report_id)
    if not done:
        print("Extraction did not complete before timeout")
        sys.exit(1)

    analysis_id = report.get("analysis_id")
    if not analysis_id:
        print("No analysis_id on report; triggering analysis")
        try:
            _ = analyze(report_id)
        except Exception as exc:  # pragma: no cover
            print(f"Failed to trigger analysis: {exc}")
            sys.exit(1)
        analysis_id, report = poll_report_for_analysis(report_id)

    if not analysis_id:
        print("Analysis id missing after trigger")
        sys.exit(1)

    print(f"Analysis id: {analysis_id}")
    analysis = poll_analysis(analysis_id)
    if analysis.get("status") != "done":
        print("Analysis did not complete before timeout")
        sys.exit(1)

    print("\n=== Analysis summary ===")
    print(f"Conditions: {len(analysis.get('conditions', []))}")
    for cond in analysis.get("conditions", []):
        print(f"- {cond.get('condition')} ({cond.get('probability')})")

    print("\nAbnormal params:")
    for param in analysis.get("abnormal_params", [])[:5]:
        print(f"- {param.get('name')}: {param.get('value')} {param.get('unit')} (range {param.get('raw_reference_range')})")

    print("\nSuccess ✅")


if __name__ == "__main__":
    main()
