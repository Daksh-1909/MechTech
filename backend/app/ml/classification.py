"""Validated Random Forest inference with an explicit uncertain outcome."""

from typing import Any

import numpy as np
from simulator.scenarios import PHASE3_LABELS

from app.core.exceptions import AppError
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, to_feature_vector


def predict_fault(
    bundle: dict[str, Any],
    features: dict[str, float],
    *,
    minimum_score: float | None = None,
) -> tuple[str, dict[str, float], float, bool]:
    if bundle.get("artifact_type") != "random_forest":
        raise AppError(
            "The registered classifier artifact has an invalid type.",
            code="MODEL_INVALID",
            status_code=409,
        )
    if bundle.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
        raise AppError(
            "The classifier uses an incompatible feature schema.",
            code="MODEL_SCHEMA_MISMATCH",
            status_code=409,
        )
    if bundle.get("feature_names") != list(FEATURE_NAMES):
        raise AppError(
            "The classifier feature order is invalid.",
            code="MODEL_FEATURES_INVALID",
            status_code=409,
        )
    if bundle.get("labels") != list(PHASE3_LABELS):
        raise AppError(
            "The classifier label set is invalid.", code="MODEL_LABELS_INVALID", status_code=409
        )
    try:
        vector = np.asarray([to_feature_vector(features)], dtype=np.float64)
    except ValueError as exc:
        raise AppError(
            "Inference features do not match the active model schema.",
            code="INVALID_FEATURES",
            status_code=422,
        ) from exc
    if not np.isfinite(vector).all():
        raise AppError(
            "Inference features must be finite.", code="INVALID_FEATURES", status_code=422
        )
    try:
        classifier = bundle["model"]
        scores = classifier.predict_proba(vector)[0]
    except Exception as exc:
        raise AppError(
            "The classifier could not score this feature window.",
            code="MODEL_INFERENCE_FAILED",
            status_code=503,
        ) from exc
    score_by_label = {
        str(label): float(score) for label, score in zip(classifier.classes_, scores, strict=True)
    }
    best_label, best_score = max(score_by_label.items(), key=lambda item: item[1])
    threshold = float(bundle.get("minimum_score", 0.4)) if minimum_score is None else minimum_score
    if not 0 <= threshold <= 1:
        raise AppError(
            "minimum_score must be between zero and one.", code="INVALID_THRESHOLD", status_code=422
        )
    uncertain = best_score < threshold
    return ("unknown" if uncertain else best_label), score_by_label, best_score, uncertain
