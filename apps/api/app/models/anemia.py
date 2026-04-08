from __future__ import annotations

from app.models.base_predictor import get_model_metadata, predict_with_fallback


def predict(params: dict[str, float], age: int, sex: str) -> dict:
    metadata = get_model_metadata("anemia")
    feature_names = metadata.get("features", [])
    classes = metadata.get("output_labels", ["Healthy", "Iron deficiency anemia"])
    version = metadata.get("version", "2026.03")

    hb = params.get("hemoglobin", 14.0)
    ferritin = params.get("ferritin", 90.0)
    condition = "No clear anemia signal"
    probability = 0.58
    severity = "low"
    if hb < 11.5:
        condition = "Iron deficiency anemia pattern"
        probability = 0.84
        severity = "high" if hb < 9 else "moderate"
    elif ferritin < 25:
        condition = "Possible early iron deficiency"
        probability = 0.72
        severity = "moderate"
    return predict_with_fallback(
        "anemia",
        version,
        params,
        age,
        sex,
        classes,
        feature_names,
        feature_names,
        (condition, probability, severity, ["hemoglobin", "ferritin", "mcv"]),
    )
