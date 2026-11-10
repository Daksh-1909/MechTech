from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import User, UserStatus
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.auth.schemas import UserResponse
from app.modules.users import service
from app.modules.users.schemas import (
    UserCreateRequest,
    UserStatusRequest,
    UserUpdateRequest,
)

router = APIRouter()

UserManager = Annotated[User, Depends(require_permission(Permission.USER_CREATE))]


def _ensure_can_view(actor: User, user_id: uuid.UUID) -> None:
    if has_permission(actor, Permission.USER_VIEW) or actor.id == user_id:
        return
    raise AppError(
        "You do not have permission to perform this action.",
        code="FORBIDDEN",
        status_code=403,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: DbSession,
    manager: UserManager,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserResponse]:
    users = service.list_users(db, limit=limit, offset=offset)
    return [auth_service.build_user_response(user) for user in users]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreateRequest,
    db: DbSession,
    manager: UserManager,
    _: CsrfProtected,
) -> UserResponse:
    user = service.create_user(
        db,
        actor=manager,
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
        organization_id=payload.organization_id,
    )
    return auth_service.build_user_response(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: DbSession, actor: CurrentUser) -> UserResponse:
    _ensure_can_view(actor, user_id)
    return auth_service.build_user_response(service.get_user(db, user_id))


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    db: DbSession,
    actor: CurrentUser,
    _: CsrfProtected,
) -> UserResponse:
    user = service.update_user(
        db,
        actor=actor,
        user_id=user_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return auth_service.build_user_response(user)


@router.patch("/{user_id}/status", response_model=UserResponse)
def set_user_status(
    user_id: uuid.UUID,
    payload: UserStatusRequest,
    db: DbSession,
    manager: UserManager,
    _: CsrfProtected,
) -> UserResponse:
    new_status = payload.status
    if new_status is None:
        new_status = UserStatus.ACTIVE.value if payload.is_active else UserStatus.SUSPENDED.value

    user = service.set_user_status(
        db,
        actor=manager,
        user_id=user_id,
        status=new_status,
    )
    return auth_service.build_user_response(user)
