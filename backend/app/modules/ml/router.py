from typing import Annotated

from fastapi import APIRouter, Depends, Query

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
from app.modules.ml.schemas import (
    AnalysisRequest,
    ModelResponse,
    PredictionResponse,
)

router = APIRouter()

ModelViewer = Annotated[User, Depends(require_permission(Permission.MODELS_VIEW))]
AnalysisRequester = Annotated[
    User,
    Depends(require_permission(Permission.ML_ANALYSIS_REQUEST)),
]


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
