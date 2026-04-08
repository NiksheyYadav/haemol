from __future__ import annotations

from app.models.base_predictor import get_model_metadata, predict_with_fallback


def predict(params: dict[str, float], age: int, sex: str) -> dict:
    metadata = get_model_metadata("diabetes")
    feature_names = metadata.get("features", [])
    classes = metadata.get("output_labels", ["No Diabetes", "Prediabetes", "Diabetes"])
    version = metadata.get("version", "2026.03")

    glucose = params.get("glucose", 90.0)
    hba1c = params.get("hba1c", 5.2)
    condition = "No clear diabetes signal"
    probability = 0.57
    severity = "low"
    if hba1c >= 6.5 or glucose >= 126:
        condition = "Diabetes mellitus pattern"
        probability = 0.88
        severity = "high" if hba1c >= 8 else "moderate"
    elif hba1c >= 5.7 or glucose >= 100:
        condition = "Prediabetes pattern"
        probability = 0.74
        severity = "moderate"
    return predict_with_fallback(
        "diabetes",
        version,
        params,
        age,
        sex,
        classes,
        feature_names,
        feature_names,
        (condition, probability, severity, ["glucose", "hba1c", "triglycerides"]),
    )
