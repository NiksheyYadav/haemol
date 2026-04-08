from __future__ import annotations

from app.models.base_predictor import get_model_metadata, predict_with_fallback


def predict(params: dict[str, float], age: int, sex: str) -> dict:
    metadata = get_model_metadata("thyroid")
    feature_names = metadata.get("features", [])
    classes = metadata.get("output_labels", ["Normal", "Hypothyroidism", "Hyperthyroidism"])
    version = metadata.get("version", "2026.03")

    tsh = params.get("tsh", 2.0)
    t4 = params.get("t4", 8.0)
    condition = "No clear thyroid signal"
    probability = 0.55
    severity = "low"
    if tsh > 4.5:
        condition = "Hypothyroidism pattern"
        probability = 0.8
        severity = "moderate"
    elif tsh < 0.3 and t4 > 12.0:
        condition = "Hyperthyroidism pattern"
        probability = 0.79
        severity = "moderate"
    return predict_with_fallback(
        "thyroid",
        version,
        params,
        age,
        sex,
        classes,
        feature_names,
        feature_names,
        (condition, probability, severity, ["tsh", "t3", "t4"]),
    )
