from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = BASE_DIR / "model_artifacts"
REGISTRY_PATH = ARTIFACT_ROOT / "registry.json"


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        logger.warning("Model registry not found at %s", REGISTRY_PATH)
        return {}
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


REGISTRY: dict[str, Any] = _load_registry()


def get_model_metadata(model_name: str) -> Dict[str, Any]:
    metadata = REGISTRY.get(model_name)
    if metadata is None:
        logger.warning("Model %s not found in registry", model_name)
        return {"features": [], "output_labels": [], "metrics": {}, "version": ""}
    return metadata


def _stable_random(name: str, payload: dict[str, float]) -> float:
    digest = hashlib.sha256(f"{name}:{json.dumps(payload, sort_keys=True)}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _load_joblib(path: Path) -> Any | None:
    if path.exists():
        try:
            return joblib.load(path)
        except Exception:
            logger.exception("Failed to load model artifact at %s; falling back to heuristic output", path)
    return None


def _resolve_model_path(model_name: str, version: str) -> Path | None:
    candidates = [
        ARTIFACT_ROOT / f"{model_name}-{version}.pkl",
        ARTIFACT_ROOT / f"{model_name}.pkl",
        ARTIFACT_ROOT / f"{model_name}-{version}.joblib",
        ARTIFACT_ROOT / f"{model_name}.joblib",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def predict_with_fallback(
    model_name: str,
    version: str,
    params: dict[str, float],
    age: int,
    sex: str,
    classes: list[str],
    feature_names: list[str],
    top_features: list[str],
    heuristic: tuple[str, float, str, list[str]],
) -> dict:
    model_path = _resolve_model_path(model_name, version)
    model = _load_joblib(model_path) if model_path else None
    if model is not None:
        try:
            ordered_features = feature_names or sorted(params)
            vector = np.array([[params.get(name, 0.0) for name in ordered_features]], dtype=float)
            predicted_classes = model.predict(vector)
            predicted_idx = int(predicted_classes[0])
            proba = getattr(model, "predict_proba", None)
            if callable(proba):
                prob_array = model.predict_proba(vector)
                probability = float(prob_array[0][predicted_idx]) if prob_array.size else 0.0
            else:
                probability = 0.0
            condition = classes[predicted_idx] if predicted_idx < len(classes) else str(predicted_idx)
            severity = "low" if probability < 0.7 else "moderate" if probability < 0.85 else "high"
            return {
                "condition": condition,
                "probability": round(probability, 3),
                "severity": severity,
                "top_features": (top_features or ordered_features)[:5],
                "model_version": version,
            }
        except Exception:
            logger.exception("Model inference failed for %s; using heuristic fallback", model_name)

    logger.warning("Missing model artifact for %s; using heuristic fallback", model_name)
    condition, probability, severity, features = heuristic
    jitter = (_stable_random(model_name, params | {"age": age, "sex": 0 if sex == "male" else 1}) - 0.5) * 0.06
    return {
        "condition": condition,
        "probability": round(max(min(probability + jitter, 0.99), 0.51), 3),
        "severity": severity,
        "top_features": features,
        "model_version": f"{version}-fallback",
    }
