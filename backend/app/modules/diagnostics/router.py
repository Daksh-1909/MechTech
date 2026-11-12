from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.diagnostics import service
from app.modules.diagnostics.schemas import (
    DiagnosisGenerateRequest,
    DiagnosisResponse,
    DiagnosisReviewRequest,
)

router = APIRouter()

DiagnosisReviewer = Annotated[
    User,
    Depends(require_permission(Permission.DIAGNOSIS_REVIEW)),
]
DiagnosisGenerator = Annotated[
    User,
    Depends(require_permission(Permission.DIAGNOSIS_GENERATE)),
]


@router.get("", response_model=list[DiagnosisResponse], tags=["diagnostics"])
def list_diagnoses(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
    equipment_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DiagnosisResponse]:
    return service.list_diagnoses(
        db,
        actor=user,
        organization_id=organization_id,
        equipment_id=equipment_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse, tags=["diagnostics"])
def get_diagnosis(
    diagnosis_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> DiagnosisResponse:
    return service.get_diagnosis(db, actor=user, diagnosis_id=diagnosis_id)


@router.post("/generate", response_model=DiagnosisResponse, status_code=201, tags=["diagnostics"])
def generate_diagnosis(
    payload: DiagnosisGenerateRequest,
    db: DbSession,
    actor: DiagnosisGenerator,
    _: CsrfProtected,
) -> DiagnosisResponse:
    return service.run_diagnosis(
        db,
        actor=actor,
        equipment_id=payload.equipment_id,
        window_size=payload.window_size,
    )


@router.post("/{diagnosis_id}/review", response_model=DiagnosisResponse, tags=["diagnostics"])
def review_diagnosis(
    diagnosis_id: uuid.UUID,
    payload: DiagnosisReviewRequest,
    db: DbSession,
    reviewer: DiagnosisReviewer,
    _: CsrfProtected,
) -> DiagnosisResponse:
    return service.review_diagnosis(
        db,
        actor=reviewer,
        diagnosis_id=diagnosis_id,
        payload=payload,
    )

