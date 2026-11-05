from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AnomalyEvent, MLPrediction, ModelRegistry


def get_prediction(db: Session, prediction_id: int) -> MLPrediction | None:
    return db.get(MLPrediction, prediction_id)


def list_predictions(
    db: Session,
    *,
    equipment_id: str | None,
    limit: int,
    offset: int,
) -> list[MLPrediction]:
    statement = select(MLPrediction)
    if equipment_id is not None:
        statement = statement.where(MLPrediction.equipment_id == equipment_id)
    statement = (
        statement.order_by(
            MLPrediction.prediction_timestamp.desc(),
            MLPrediction.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


def list_anomalies(
    db: Session,
    *,
    equipment_id: str,
    limit: int,
    offset: int,
) -> list[AnomalyEvent]:
    statement = (
        select(AnomalyEvent)
        .where(AnomalyEvent.equipment_id == equipment_id)
        .order_by(AnomalyEvent.start_timestamp.desc(), AnomalyEvent.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


def get_model(db: Session, model_id: int) -> ModelRegistry | None:
    return db.get(ModelRegistry, model_id)


def get_active_model(db: Session, model_type: str) -> ModelRegistry | None:
    return db.scalar(
        select(ModelRegistry)
        .where(
            ModelRegistry.model_type == model_type,
            ModelRegistry.is_active.is_(True),
        )
        .order_by(ModelRegistry.created_at.desc())
        .limit(1)
    )


def list_models(db: Session, *, model_type: str | None) -> list[ModelRegistry]:
    statement = select(ModelRegistry)
    if model_type is not None:
        statement = statement.where(ModelRegistry.model_type == model_type)
    statement = statement.order_by(ModelRegistry.created_at.desc(), ModelRegistry.id.desc())
    return list(db.scalars(statement))


def get_model_by_name_version(
    db: Session,
    *,
    model_name: str,
    model_version: str,
) -> ModelRegistry | None:
    return db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.model_name == model_name,
            ModelRegistry.model_version == model_version,
        )
    )


def deactivate_models(db: Session, *, model_type: str) -> None:
    db.execute(
        update(ModelRegistry)
        .where(
            ModelRegistry.model_type == model_type,
            ModelRegistry.is_active.is_(True),
        )
        .values(is_active=False)
    )
