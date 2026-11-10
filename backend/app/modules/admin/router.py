from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.admin.schemas import (
    AdminCreateUserRequest,
    ApproveRegistrationRequest,
    RegistrationResponse,
    RejectRegistrationRequest,
)
from app.modules.auth import service
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.auth.schemas import UserResponse

router = APIRouter()

AdminUser = Annotated[User, Depends(require_permission(Permission.USER_APPROVE))]
CreatorUser = Annotated[User, Depends(require_permission(Permission.USER_CREATE))]


@router.get("/registrations", response_model=list[RegistrationResponse])
def list_registrations(
    db: DbSession,
    admin: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RegistrationResponse]:
    requests = service.list_pending_registrations(db, limit=limit, offset=offset)
    return [
        RegistrationResponse(
            id=req.id,
            user_id=req.user_id,
            email=req.user.email,
            display_name=req.user.display_name,
            status=req.status,
            created_at=req.created_at,
            reviewed_at=req.reviewed_at,
            reviewed_by=req.reviewed_by,
            review_note=req.review_note,
        )
        for req in requests
    ]


@router.post("/registrations/{request_id}/approve", response_model=RegistrationResponse)
def approve_registration(
    request_id: uuid.UUID,
    payload: ApproveRegistrationRequest,
    db: DbSession,
    admin: AdminUser,
    _: CsrfProtected,
) -> RegistrationResponse:
    req, user = service.approve_registration(
        db,
        admin_user=admin,
        request_id=request_id,
        organization_id=payload.organization_id,
        role_key=payload.role_key,
        review_note=payload.review_note,
    )
    return RegistrationResponse(
        id=req.id,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=req.status,
        created_at=req.created_at,
        reviewed_at=req.reviewed_at,
        reviewed_by=req.reviewed_by,
        review_note=req.review_note,
    )


@router.post("/registrations/{request_id}/reject", response_model=RegistrationResponse)
def reject_registration(
    request_id: uuid.UUID,
    payload: RejectRegistrationRequest,
    db: DbSession,
    admin: AdminUser,
    _: CsrfProtected,
) -> RegistrationResponse:
    req = service.reject_registration(
        db,
        admin_user=admin,
        request_id=request_id,
        review_note=payload.review_note,
    )
    return RegistrationResponse(
        id=req.id,
        user_id=req.user_id,
        email=req.user.email,
        display_name=req.user.display_name,
        status=req.status,
        created_at=req.created_at,
        reviewed_at=req.reviewed_at,
        reviewed_by=req.reviewed_by,
        review_note=req.review_note,
    )


@router.post("/users", response_model=UserResponse, status_code=201)
def admin_create_user(
    payload: AdminCreateUserRequest,
    db: DbSession,
    admin: CreatorUser,
    _: CsrfProtected,
) -> UserResponse:
    user = service.create_user(
        db,
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
        organization_id=payload.organization_id,
    )
    return service.build_user_response(user)

