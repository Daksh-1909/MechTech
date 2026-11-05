import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.ml.features import FEATURE_SCHEMA_VERSION, build_features, to_feature_vector
from app.ml.service import load_artifact, predict_classification
from app.models import MLPrediction, ModelRegistry, User
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


def list_models(db: Session, *, model_type: str | None) -> list[ModelRegistry]:
    return repository.list_models(db, model_type=model_type)


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

    from app.ml.service import resolve_artifact_path

    resolve_artifact_path(artifact_path)

    if model_type == ModelType.ANOMALY:
        repository.deactivate_models(db, model_type=ModelType.ANOMALY.value)
    elif model_type == ModelType.CLASSIFICATION:
        repository.deactivate_models(db, model_type=ModelType.CLASSIFICATION.value)

    entry = ModelRegistry(
        model_name=model_name,
        model_version=model_version,
        model_type=model_type.value,
        artifact_path=artifact_path,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        training_dataset_description=training_dataset_description,
        evaluation_metrics_json=evaluation_metrics_json,
        is_active=True,
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


def analyze_equipment(
    db: Session,
    *,
    equipment_id: str,
    window_size: int,
) -> MLPrediction:
    equipment = equipment_repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)

    readings = sensor_repository.list_recent_readings(
        db,
        equipment_id=equipment_id,
        limit=window_size,
    )
    if len(readings) < 2:
        raise AppError(
            "At least two readings are required for analysis.",
            code="INSUFFICIENT_DATA",
            status_code=409,
        )

    features = build_features(readings)
    feature_vector = to_feature_vector(features)
    reading_ids = [reading.id for reading in readings]
    db.commit()

    model_entry = repository.get_active_model(db, ModelType.CLASSIFICATION.value)
    if model_entry is None:
        raise AppError(
            "No active classification model is available.",
            code="MODEL_UNAVAILABLE",
            status_code=503,
        )

    try:
        model = load_artifact(model_entry.artifact_path)
        predicted_class, probabilities, confidence = predict_classification(
            model,
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

    prediction = MLPrediction(
        equipment_id=equipment_id,
        model_registry_id=model_entry.id,
        predicted_class=predicted_class,
        probabilities_json=probabilities,
        confidence_value=confidence,
        evidence_json={
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "window_size": len(readings),
            "reading_ids": reading_ids,
            "features": features,
            "note": "Prediction based on simulated data; not a confirmed diagnosis.",
        },
        prediction_timestamp=utcnow(),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
