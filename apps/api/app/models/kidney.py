from __future__ import annotations

from app.models.base_predictor import get_model_metadata, predict_with_fallback


def predict(params: dict[str, float], age: int, sex: str) -> dict:
    metadata = get_model_metadata("kidney")
    feature_names = metadata.get("features", [])
    classes = metadata.get("output_labels", ["No CKD", "CKD"])
    version = metadata.get("version", "2026.03")

    creatinine = params.get("creatinine", 1.0)
    bun = params.get("blood urea nitrogen", 14.0)
    condition = "No clear kidney signal"
    probability = 0.56
    severity = "low"
    if creatinine >= 1.6 or bun >= 30:
        condition = "Chronic kidney disease pattern"
        probability = 0.81
        severity = "high" if creatinine >= 2.2 else "moderate"
    return predict_with_fallback(
        "kidney",
        version,
        params,
        age,
        sex,
        classes,
        feature_names,
        feature_names,
        (condition, probability, severity, ["creatinine", "blood urea nitrogen", "sodium"]),
    )
