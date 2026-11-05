from __future__ import annotations

import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import DbSession
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.permissions import Permission, ensure_permission
from app.core.security import verify_token
from app.models import User, UserSession
from app.modules.auth import service


def _unauthorized() -> AppError:
    return AppError("Authentication required.", code="UNAUTHORIZED", status_code=401)


def get_current_session(request: Request, db: DbSession) -> UserSession:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise _unauthorized()

    session = service.get_active_session(db, raw_token)
    if session is None:
        raise _unauthorized()
    return session


def get_current_user(
    session: Annotated[UserSession, Depends(get_current_session)],
) -> User:
    return session.user


def validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise AppError(
            "Untrusted request origin.",
            code="CSRF_FAILED",
            status_code=403,
        )


def require_csrf(
    request: Request,
    session: Annotated[UserSession, Depends(get_current_session)],
) -> None:
    validate_origin(request)

    provided = request.headers.get(settings.csrf_header_name)
    if not provided or not verify_token(provided, session.csrf_token_hash):
        raise AppError(
            "CSRF validation failed.",
            code="CSRF_FAILED",
            status_code=403,
        )


def require_ingestion_access(request: Request, db: DbSession) -> None:
    if settings.simulator_api_key:
        provided = request.headers.get(settings.device_api_key_header)
        if provided and hmac.compare_digest(provided, settings.simulator_api_key):
            return

    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise _unauthorized()

    session = service.get_active_session(db, raw_token)
    if session is None:
        raise _unauthorized()

    ensure_permission(session.user, Permission.READINGS_INGEST)


IngestionAccess = Annotated[None, Depends(require_ingestion_access)]


def require_permission(permission: Permission) -> Callable[[CurrentUser], User]:
    def dependency(user: CurrentUser) -> User:
        ensure_permission(user, permission)
        return user

    return dependency


CurrentSession = Annotated[UserSession, Depends(get_current_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CsrfProtected = Annotated[None, Depends(require_csrf)]
