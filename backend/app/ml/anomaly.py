"""Isolation Forest fitting, safe inference inputs and anomaly evidence persistence."""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, to_feature_vector
from app.ml.service import load_registered_artifact
from app.models import AnomalyEvent, ModelRegistry


@dataclass(frozen=True, slots=True)
class AnomalyResult:
    is_anomaly: bool
    score: float
    decision_threshold: float
    detector_name: str
    model_version: str
    evidence: dict[str, Any]


def train_isolation_forest(
    normal_windows: list[dict[str, float]],
    *,
    seed: int,
    contamination: float = 0.05,
) -> dict[str, Any]:
    if len(normal_windows) < 10:
        raise ValueError("At least ten normal feature windows are required.")
    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be greater than zero and at most 0.5.")
    vectors = [to_feature_vector(window) for window in normal_windows]
    matrix = np.asarray(vectors, dtype=np.float64)
    if not np.isfinite(matrix).all():
        raise ValueError("Training features must all be finite.")
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=seed,
        n_jobs=1,
    )
    model.fit(matrix)
    means = matrix.mean(axis=0)
    standard_deviations = matrix.std(axis=0)
    return {
        "artifact_type": "isolation_forest",
        "model": model,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "training_mean": means.tolist(),
        "training_standard_deviation": standard_deviations.tolist(),
        "decision_threshold": 0.0,
        "contamination": contamination,
        "random_state": seed,
    }


def score_window(
    bundle: dict[str, Any],
    features: dict[str, float],
    *,
    model_version: str,
) -> AnomalyResult:
    if bundle.get("artifact_type") != "isolation_forest":
        raise AppError(
            "The registered anomaly artifact has an invalid type.",
            code="MODEL_INVALID",
            status_code=409,
        )
    if bundle.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
        raise AppError(
            "The anomaly model uses an incompatible feature schema.",
            code="MODEL_SCHEMA_MISMATCH",
            status_code=409,
        )
    if bundle.get("feature_names") != list(FEATURE_NAMES):
        raise AppError(
            "The anomaly model feature order is invalid.",
            code="MODEL_FEATURES_INVALID",
            status_code=409,
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
    model = bundle.get("model")
    try:
        decision = float(model.decision_function(vector)[0])
        raw_score = float(model.score_samples(vector)[0])
        is_anomaly = int(model.predict(vector)[0]) == -1
    except Exception as exc:
        raise AppError(
            "The anomaly model could not score this feature window.",
            code="MODEL_INFERENCE_FAILED",
            status_code=503,
        ) from exc

    means = np.asarray(bundle["training_mean"], dtype=np.float64)
    stds = np.asarray(bundle["training_standard_deviation"], dtype=np.float64)
    values = vector[0]
    deviations = []
    for index, name in enumerate(FEATURE_NAMES):
        std = float(stds[index])
        difference = float(values[index] - means[index])
        z_score = difference / std if std > 0 else None
        deviations.append(
            {
                "feature": name,
                "value": float(values[index]),
                "normal_training_mean": float(means[index]),
                "normal_training_std": std,
                "standardized_deviation": z_score,
                "absolute_deviation": abs(z_score) if z_score is not None else abs(difference),
            }
        )
    deviations.sort(key=lambda item: item["absolute_deviation"], reverse=True)
    return AnomalyResult(
        is_anomaly=is_anomaly,
        score=raw_score,
        decision_threshold=float(bundle.get("decision_threshold", 0.0)),
        detector_name="isolation_forest",
        model_version=model_version,
        evidence={
            "decision_score": decision,
            "score_semantics": "raw Isolation Forest score; lower values are more unusual",
            "top_feature_deviations": deviations[:5],
        },
    )


def infer_registered_model(
    model_entry: ModelRegistry,
    features: dict[str, float],
) -> AnomalyResult:
    artifact = load_registered_artifact(model_entry)
    if not isinstance(artifact, dict):
        raise AppError(
            "The registered anomaly artifact is invalid.", code="MODEL_INVALID", status_code=409
        )
    return score_window(artifact, features, model_version=model_entry.model_version)


def persist_anomaly_event(
    db: Session,
    *,
    equipment_id: str,
    feature_window_id: int,
    window_start: datetime,
    window_end: datetime,
    result: AnomalyResult,
) -> AnomalyEvent | None:
    if not result.is_anomaly:
        return None
    if not math.isfinite(result.score):
        raise AppError("Anomaly score is non-finite.", code="INVALID_SCORE", status_code=422)
    existing = db.scalar(
        select(AnomalyEvent).where(
            AnomalyEvent.equipment_id == equipment_id,
            AnomalyEvent.feature_window_id == feature_window_id,
            AnomalyEvent.detector_name == result.detector_name,
            AnomalyEvent.model_version == result.model_version,
            AnomalyEvent.event_type == "ml_anomaly",
        )
    )
    if existing is not None:
        return existing
    event = AnomalyEvent(
        equipment_id=equipment_id,
        feature_window_id=feature_window_id,
        event_type="ml_anomaly",
        severity="medium",
        start_timestamp=window_start,
        end_timestamp=window_end,
        anomaly_score=result.score,
        description="Isolation Forest marked this feature window as unusual; advisory only.",
        evidence_json={
            "detector_name": result.detector_name,
            "model_version": result.model_version,
            "decision_threshold": result.decision_threshold,
            **result.evidence,
        },
        detector_name=result.detector_name,
        model_version=result.model_version,
    )
    db.add(event)
    db.flush()
    return event
