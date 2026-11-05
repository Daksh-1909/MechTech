from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.models.enums import ModelType
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.ml import service
from app.modules.ml import training as training_service
from app.modules.ml.schemas import (
    AnalysisRequest,
    AnomalyResponse,
    ModelResponse,
    PredictionResponse,
    TrainingJobCreateRequest,
    TrainingJobResponse,
)

router = APIRouter()

ModelViewer = Annotated[User, Depends(require_permission(Permission.MODELS_VIEW))]
AnalysisRequester = Annotated[
    User,
    Depends(require_permission(Permission.ML_ANALYSIS_REQUEST)),
]
ModelManager = Annotated[User, Depends(require_permission(Permission.MODEL_MANAGE))]


@router.get("/predictions", response_model=list[PredictionResponse])
def list_predictions(
    db: DbSession,
    user: CurrentUser,
    equipment_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PredictionResponse]:
    predictions = service.list_predictions(
        db,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )
    return [PredictionResponse.model_validate(item) for item in predictions]


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    db: DbSession,
    user: CurrentUser,
) -> PredictionResponse:
    return PredictionResponse.model_validate(service.get_prediction(db, prediction_id))


@router.get(
    "/equipment/{equipment_id}/predictions",
    response_model=list[PredictionResponse],
)
def list_equipment_predictions(
    equipment_id: str,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PredictionResponse]:
    items = service.list_equipment_predictions(
        db,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )
    return [PredictionResponse.model_validate(item) for item in items]


@router.get(
    "/equipment/{equipment_id}/anomalies",
    response_model=list[AnomalyResponse],
)
def list_equipment_anomalies(
    equipment_id: str,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AnomalyResponse]:
    items = service.list_equipment_anomalies(
        db,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )
    return [AnomalyResponse.model_validate(item) for item in items]


@router.get("/models", response_model=list[ModelResponse])
def list_models(
    db: DbSession,
    viewer: ModelViewer,
    model_type: ModelType | None = None,
) -> list[ModelResponse]:
    models = service.list_models(
        db,
        model_type=None if model_type is None else model_type.value,
    )
    return [ModelResponse.model_validate(item) for item in models]


@router.post("/models/{model_id}/activate", response_model=ModelResponse)
def activate_model(
    model_id: int,
    db: DbSession,
    manager: ModelManager,
    _: CsrfProtected,
) -> ModelResponse:
    model_entry = service.get_model(db, model_id)
    activated = service.activate_model(db, actor=manager, model_entry=model_entry)
    return ModelResponse.model_validate(activated)


@router.post("/equipment/{equipment_id}/analysis", response_model=PredictionResponse)
def analyze_equipment(
    equipment_id: str,
    payload: AnalysisRequest,
    db: DbSession,
    requester: AnalysisRequester,
    _: CsrfProtected,
) -> PredictionResponse:
    prediction = service.analyze_equipment(
        db,
        equipment_id=equipment_id,
        window_size=payload.window_size,
    )
    return PredictionResponse.model_validate(prediction)


@router.post("/train", response_model=TrainingJobResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_training_job(
    payload: TrainingJobCreateRequest,
    db: DbSession,
    manager: ModelManager,
    _: CsrfProtected,
) -> TrainingJobResponse:
    parameters = payload.model_dump(exclude={"model_type"})
    if payload.model_type == ModelType.ANOMALY:
        parameters.pop("minimum_score")
    else:
        parameters.pop("contamination")
    job = training_service.submit_job(
        db, actor=manager, model_type=payload.model_type, parameters=parameters
    )
    return TrainingJobResponse.model_validate(job)


@router.get("/training-jobs/{job_id}", response_model=TrainingJobResponse)
def get_training_job(
    job_id: str,
    db: DbSession,
    manager: ModelManager,
) -> TrainingJobResponse:
    return TrainingJobResponse.model_validate(training_service.get_job(db, job_id))
