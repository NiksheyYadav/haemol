from __future__ import annotations

from app.models.base_predictor import get_model_metadata, predict_with_fallback


def predict(params: dict[str, float], age: int, sex: str) -> dict:
    metadata = get_model_metadata("liver")
    feature_names = metadata.get("features", [])
    classes = metadata.get("output_labels", ["Normal", "Liver Disease"])
    version = metadata.get("version", "2026.03")

    alt = params.get("alt", 25.0)
    ast = params.get("ast", 24.0)
    bilirubin = params.get("total bilirubin", 0.8)
    condition = "No clear liver signal"
    probability = 0.59
    severity = "low"
    if alt >= 80 or ast >= 80 or bilirubin >= 2:
        condition = "Liver disease pattern"
        probability = 0.85
        severity = "high" if max(alt, ast) >= 140 else "moderate"
    return predict_with_fallback(
        "liver",
        version,
        params,
        age,
        sex,
        classes,
        feature_names,
        feature_names,
        (condition, probability, severity, ["alt", "ast", "total bilirubin"]),
    )
