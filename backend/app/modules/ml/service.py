import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.ml.features import FEATURE_SCHEMA_VERSION, build_features, to_feature_vector
from app.ml.service import load_artifact, load_registered_artifact, predict_classification
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
        or model_entry.feature_schema_version != FEATURE_SCHEMA_VERSION
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
