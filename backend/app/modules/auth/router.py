from datetime import datetime
import uuid

from fastapi import APIRouter, Request, Response

from app.api.deps import DbSession
from app.core.config import settings
from app.core.time import utcnow
from app.modules.audit.actions import AuditAction
from app.modules.auth import service
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentSession,
    CurrentUser,
    validate_origin,
)
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
    UserResponse,
)

router = APIRouter()


def _cookie_max_age(expires_at: datetime) -> int:
    return max(0, int((expires_at - utcnow()).total_seconds()))


def _set_session_cookies(
    response: Response,
    *,
    raw_token: str,
    csrf_token: str,
    expires_at: datetime,
) -> None:
    max_age = _cookie_max_age(expires_at)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    for name, httponly in (
        (settings.session_cookie_name, True),
        (settings.csrf_cookie_name, False),
    ):
        response.delete_cookie(
            key=name,
            httponly=httponly,
            secure=settings.session_cookie_secure,
            samesite=settings.session_cookie_samesite,
            path="/",
        )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    db: DbSession,
) -> RegisterResponse:
    validate_origin(request)
    user, _ = service.register_user(
        db,
        display_name=payload.display_name,
        email=str(payload.email),
        password=payload.password,
        organization_name=payload.organization_name,
    )
    return RegisterResponse(
        message="Registration submitted successfully. Your account is pending administrator approval.",
        user_id=user.id,
        status=user.status,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> LoginResponse:
    validate_origin(request)

    user = service.authenticate(db, email=str(payload.email), password=payload.password)
    raw_token, csrf_token, session = service.create_session(
        db,
        user=user,
        user_agent=request.headers.get("user-agent"),
    )
    _set_session_cookies(
        response,
        raw_token=raw_token,
        csrf_token=csrf_token,
        expires_at=session.expires_at,
    )
    return LoginResponse(
        user=service.build_user_response(user),
        csrf_token=csrf_token,
        expires_at=session.expires_at,
    )


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    db: DbSession,
    session: CurrentSession,
    _: CsrfProtected,
) -> None:
    service.revoke_session(db, session=session, action=AuditAction.AUTH_LOGOUT)
    _clear_session_cookies(response)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return service.build_user_response(user)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: DbSession,
    user: CurrentUser,
    session: CurrentSession,
) -> list[SessionResponse]:
    sessions = service.list_sessions(db, user=user)
    return [
        SessionResponse.model_validate(item).model_copy(
            update={"is_current": item.id == session.id}
        )
        for item in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    _: CsrfProtected,
) -> None:
    service.revoke_owned_session(db, user=user, session_id=session_id)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: DbSession,
    user: CurrentUser,
    session: CurrentSession,
    _: CsrfProtected,
) -> MessageResponse:
    service.change_password(
        db,
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        current_session_id=session.id,
    )
    return MessageResponse(message="Password changed.")
