import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.time import utcnow
from app.ml.anomaly import infer_registered_model, persist_anomaly_event
from app.ml.baseline import (
    compare_features,
    get_active_baseline,
    persist_baseline_event,
)
from app.ml.classification import predict_fault
from app.ml.datasets import SYNTHETIC_LABELS
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    build_features,
    persist_window,
    segment_readings,
    to_feature_vector,
)
from app.ml.service import load_registered_artifact, predict_classification
from app.models import AnomalyEvent, MLPrediction, ModelRegistry, User
from app.models.enums import ModelType
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository as equipment_repository
from app.modules.ml import repository
from app.modules.sensors import repository as sensor_repository

logger = logging.getLogger(__name__)


def get_prediction(db: Session, prediction_id: int) -> MLPrediction:
    prediction = repository.get_prediction(db, prediction_id)
    if prediction is None:
        raise AppError("Prediction not found.", code="NOT_FOUND", status_code=404)
    return prediction


def list_predictions(
    db: Session,
    *,
    equipment_id: str | None,
    limit: int,
    offset: int,
) -> list[MLPrediction]:
    return repository.list_predictions(
        db,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )


def list_equipment_predictions(
    db: Session,
    *,
    equipment_id: str,
    limit: int,
    offset: int,
) -> list[MLPrediction]:
    if equipment_repository.get_equipment(db, equipment_id) is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return list_predictions(db, equipment_id=equipment_id, limit=limit, offset=offset)


def list_equipment_anomalies(
    db: Session,
    *,
    equipment_id: str,
    limit: int,
    offset: int,
) -> list[AnomalyEvent]:
    if equipment_repository.get_equipment(db, equipment_id) is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return repository.list_anomalies(
        db,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )


def list_models(db: Session, *, model_type: str | None) -> list[ModelRegistry]:
    return repository.list_models(db, model_type=model_type)


def get_model(db: Session, model_id: int) -> ModelRegistry:
    model_entry = repository.get_model(db, model_id)
    if model_entry is None:
        raise AppError("Model not found.", code="NOT_FOUND", status_code=404)
    return model_entry


def register_model(
    db: Session,
    *,
    actor: User,
    model_name: str,
    model_version: str,
    model_type: ModelType,
    artifact_path: str,
    training_dataset_description: str | None,
    evaluation_metrics_json: dict | None,
    training_dataset_version: str | None = None,
    activate: bool = True,
) -> ModelRegistry:
    if (
        repository.get_model_by_name_version(
            db,
            model_name=model_name,
            model_version=model_version,
        )
        is not None
    ):
        raise AppError(
            "This model version is already registered.",
            code="MODEL_EXISTS",
            status_code=409,
        )

    from app.ml.service import artifact_sha256, resolve_artifact_path

    artifact = resolve_artifact_path(artifact_path)
    checksum = artifact_sha256(artifact)
    if activate:
        repository.deactivate_models(db, model_type=model_type.value)

    entry = ModelRegistry(
        model_name=model_name,
        model_version=model_version,
        model_type=model_type.value,
        artifact_path=artifact_path,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        training_dataset_description=training_dataset_description,
        evaluation_metrics_json=evaluation_metrics_json,
        training_dataset_version=training_dataset_version,
        artifact_sha256=checksum,
        is_active=activate,
    )
    db.add(entry)
    db.flush()
    audit_service.record_event(
        db,
        action=AuditAction.MODEL_REGISTERED,
        resource_type="model",
        resource_id=entry.id,
        actor_user_id=actor.id,
        metadata={"model_name": model_name, "model_type": model_type.value},
    )
    db.commit()
    db.refresh(entry)
    return entry


def activate_model(db: Session, *, actor: User, model_entry: ModelRegistry) -> ModelRegistry:
    artifact = load_registered_artifact(model_entry)
    expected_type = {
        ModelType.ANOMALY.value: "isolation_forest",
        ModelType.CLASSIFICATION.value: "random_forest",
    }.get(model_entry.model_type)
    if (
        not isinstance(artifact, dict)
        or artifact.get("artifact_type") != expected_type
        or artifact.get("feature_schema_version") != FEATURE_SCHEMA_VERSION
        or artifact.get("feature_names") != list(FEATURE_NAMES)
        or model_entry.feature_schema_version != FEATURE_SCHEMA_VERSION
        or not hasattr(artifact.get("model"), "predict")
        or (
            expected_type == "random_forest"
            and (
                not hasattr(artifact.get("model"), "predict_proba")
                or artifact.get("labels") != list(SYNTHETIC_LABELS)
            )
        )
        or (
            expected_type == "isolation_forest"
            and (
                not hasattr(artifact.get("model"), "decision_function")
                or not hasattr(artifact.get("model"), "score_samples")
            )
        )
    ):
        raise AppError(
            "The model artifact metadata is incompatible and cannot be activated.",
            code="MODEL_METADATA_INVALID",
            status_code=409,
        )
    repository.deactivate_models(db, model_type=model_entry.model_type)
    model_entry.is_active = True
    audit_service.record_event(
        db,
        action=AuditAction.MODEL_ACTIVATED,
        resource_type="model",
        resource_id=model_entry.id,
        actor_user_id=actor.id,
        metadata={"model_name": model_entry.model_name, "model_type": model_entry.model_type},
    )
    db.commit()
    db.refresh(model_entry)
    return model_entry


def analyze_equipment(
    db: Session,
    *,
    equipment_id: str,
    window_size: int,
) -> MLPrediction:
    equipment = equipment_repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)

    recent = sensor_repository.list_recent_readings(
        db,
        equipment_id=equipment_id,
        limit=max(2, window_size),
    )
    if len(recent) < 2:
        raise AppError(
            "At least two readings are required for analysis.",
            code="INSUFFICIENT_DATA",
            status_code=409,
        )

    model_entry = repository.get_active_model(db, ModelType.CLASSIFICATION.value)
    if model_entry is None:
        raise AppError(
            "No active classification model is available.",
            code="MODEL_UNAVAILABLE",
            status_code=503,
        )

    try:
        artifact = load_registered_artifact(model_entry)
        is_phase3_classifier = (
            isinstance(artifact, dict) and artifact.get("artifact_type") == "random_forest"
        )
        stored_window = None
        if is_phase3_classifier:
            readings = sensor_repository.list_recent_readings(
                db,
                equipment_id=equipment_id,
                limit=settings.analysis_window_max,
            )
            complete_windows = [window for window in segment_readings(readings) if window.complete]
            if not complete_windows:
                raise AppError(
                    "No complete feature window is available for analysis.",
                    code="INSUFFICIENT_DATA",
                    status_code=409,
                )
            selected_window = complete_windows[-1]
            stored_window = persist_window(db, selected_window)
            features = selected_window.features
            window_start = selected_window.window_start
            window_end = selected_window.window_end
            reading_ids = list(selected_window.source_reading_ids)
        else:
            readings = recent
            features = build_features(readings)
            window_start = readings[0].timestamp
            window_end = readings[-1].timestamp
            reading_ids = [reading.id for reading in readings]

        uncertain = False
        anomaly_summary = None
        anomaly_event = None
        if is_phase3_classifier:
            predicted_class, probabilities, confidence, uncertain = predict_fault(
                artifact,
                features,
            )
            if stored_window is None:
                raise AppError(
                    "Feature window was not persisted.", code="WINDOW_MISSING", status_code=500
                )

            active_anomaly_model = repository.get_active_model(db, ModelType.ANOMALY.value)
            active_baseline = get_active_baseline(db)
            isolation_result = None
            baseline_result = None
            if active_anomaly_model is not None:
                isolation_result = infer_registered_model(active_anomaly_model, features)
                if isolation_result.is_anomaly:
                    anomaly_event = persist_anomaly_event(
                        db,
                        equipment_id=equipment_id,
                        feature_window_id=stored_window.id,
                        window_start=window_start,
                        window_end=window_end,
                        result=isolation_result,
                    )
            if active_baseline is not None:
                baseline_result = compare_features(features, active_baseline)
                if baseline_result.is_anomaly:
                    baseline_event = persist_baseline_event(
                        db,
                        equipment_id=equipment_id,
                        feature_window_id=stored_window.id,
                        window_start=window_start,
                        window_end=window_end,
                        result=baseline_result,
                    )
                    anomaly_event = anomaly_event or baseline_event

            if isolation_result is not None or baseline_result is not None:
                anomaly_summary = {
                    "is_anomaly": bool(
                        (isolation_result and isolation_result.is_anomaly)
                        or (baseline_result and baseline_result.is_anomaly)
                    ),
                    "isolation_forest": (
                        None
                        if isolation_result is None
                        else {
                            "is_anomaly": isolation_result.is_anomaly,
                            "score": isolation_result.score,
                            "decision_threshold": isolation_result.decision_threshold,
                            "detector_name": isolation_result.detector_name,
                            "model_version": isolation_result.model_version,
                            "evidence": isolation_result.evidence,
                        }
                    ),
                    "statistical_baseline": (
                        None
                        if baseline_result is None
                        else {
                            "is_anomaly": baseline_result.is_anomaly,
                            "baseline_version": baseline_result.baseline_version,
                            "threshold": baseline_result.threshold,
                            "evidence": baseline_result.evidence,
                        }
                    ),
                }
        else:
            feature_vector = to_feature_vector(features)
            predicted_class, probabilities, confidence = predict_classification(
                artifact,
                feature_vector,
            )
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Model inference failed for model %s", model_entry.id)
        raise AppError(
            "The active model could not produce a prediction.",
            code="MODEL_INFERENCE_FAILED",
            status_code=503,
        ) from exc

    explanation = []
    if anomaly_summary and anomaly_summary["is_anomaly"]:
        explanation.append(
            "The selected feature window differs from its configured normal reference."
        )
    if uncertain:
        explanation.append(
            "Classifier evidence is below the configured score threshold; label is unknown."
        )
    if not explanation:
        if is_phase3_classifier and anomaly_summary is None:
            explanation.append("No trained anomaly detector or baseline is active for this run.")
        elif is_phase3_classifier:
            explanation.append("No active anomaly detector flagged this feature window.")
        else:
            explanation.append(
                "Legacy classifier output; Phase 3 anomaly results were not calculated."
            )

    prediction = MLPrediction(
        equipment_id=equipment_id,
        anomaly_event_id=anomaly_event.id if anomaly_event is not None else None,
        model_registry_id=model_entry.id,
        feature_window_id=stored_window.id if stored_window is not None else None,
        window_start=window_start,
        window_end=window_end,
        training_dataset_version=model_entry.training_dataset_version,
        predicted_class=predicted_class,
        probabilities_json=probabilities,
        confidence_value=confidence,
        evidence_json={
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "window_size": len(readings),
            "reading_ids": reading_ids,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "features": features,
            "uncertain": uncertain,
            "anomaly_result": anomaly_summary,
            "explanations": explanation,
            "model_version": model_entry.model_version,
            "training_dataset_version": model_entry.training_dataset_version,
            "evaluation_metrics": model_entry.evaluation_metrics_json,
            "score_semantics": (
                "Random Forest class scores; not calibrated fault probabilities."
                if is_phase3_classifier
                else "Legacy classifier output; interpret as advisory only."
            ),
            "note": "Prediction based on simulated data; not a confirmed diagnosis.",
        },
        prediction_timestamp=utcnow(),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
