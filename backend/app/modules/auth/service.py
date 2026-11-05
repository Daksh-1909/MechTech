from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    is_acceptable_password,
    verify_password,
)
from app.core.time import utcnow
from app.models import User, UserRole, UserSession
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository

_LAST_SEEN_UPDATE_INTERVAL = timedelta(minutes=5)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.OPERATOR,
    commit: bool = True,
) -> User:
    normalized_email = normalize_email(email)

    if repository.get_user_by_email(db, normalized_email) is not None:
        raise AppError(
            "A user with this email already exists.",
            code="EMAIL_IN_USE",
            status_code=409,
        )

    if not is_acceptable_password(password):
        raise AppError(
            "Password must be between 12 and 128 characters.",
            code="WEAK_PASSWORD",
            status_code=400,
        )

    user = repository.create_user_record(
        db,
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
    )
    if commit:
        db.commit()
        db.refresh(user)
    else:
        db.flush()
    return user


def create_initial_admin(db: Session, *, name: str, email: str, password: str) -> User:
    if repository.admin_exists(db):
        raise AppError(
            "An administrator already exists.",
            code="ADMIN_EXISTS",
            status_code=409,
        )
    return create_user(db, name=name, email=email, password=password, role=UserRole.ADMIN)


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = repository.get_user_by_email(db, normalize_email(email))
    if user is None or not verify_password(password, user.password_hash) or not user.is_active:
        audit_service.record_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            resource_type="auth",
            actor_user_id=user.id if user is not None else None,
            metadata={"reason": "invalid_credentials"},
        )
        db.commit()
        raise AppError(
            "Invalid email or password.",
            code="INVALID_CREDENTIALS",
            status_code=401,
        )
    return user


def create_session(
    db: Session,
    *,
    user: User,
    user_agent: str | None,
) -> tuple[str, str, UserSession]:
    raw_token = generate_token()
    csrf_token = generate_token()
    expires_at = utcnow() + timedelta(hours=settings.session_ttl_hours)
    user_agent_summary = user_agent[:255] if user_agent else None

    session = repository.create_session_record(
        db,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=expires_at,
        user_agent_summary=user_agent_summary,
    )
    audit_service.record_event(
        db,
        action=AuditAction.AUTH_LOGIN_SUCCEEDED,
        resource_type="session",
        resource_id=session.id,
        actor_user_id=user.id,
        metadata={"role": user.role},
    )
    db.commit()
    db.refresh(session)
    return raw_token, csrf_token, session


def get_active_session(db: Session, raw_token: str) -> UserSession | None:
    session = repository.get_session_by_token_hash(db, hash_token(raw_token))
    if session is None:
        return None

    now = utcnow()
    if session.revoked_at is not None or session.expires_at <= now:
        return None
    if not session.user.is_active:
        return None

    if now - session.last_seen_at >= _LAST_SEEN_UPDATE_INTERVAL:
        session.last_seen_at = now
        db.commit()

    return session


def revoke_session(
    db: Session,
    *,
    session: UserSession,
    action: str = AuditAction.AUTH_SESSION_REVOKED,
) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        audit_service.record_event(
            db,
            action=action,
            resource_type="session",
            resource_id=session.id,
            actor_user_id=session.user_id,
        )
        db.commit()


def list_sessions(db: Session, *, user: User) -> list[UserSession]:
    return repository.list_sessions_for_user(db, user.id)


def revoke_owned_session(db: Session, *, user: User, session_id: int) -> None:
    session = repository.get_session_for_user(db, session_id=session_id, user_id=user.id)
    if session is None:
        raise AppError("Session not found.", code="NOT_FOUND", status_code=404)
    revoke_session(db, session=session)


def change_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
    current_session_id: int,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AppError(
            "Current password is incorrect.",
            code="INVALID_PASSWORD",
            status_code=400,
        )

    if not is_acceptable_password(new_password):
        raise AppError(
            "Password must be between 12 and 128 characters.",
            code="WEAK_PASSWORD",
            status_code=400,
        )

    if verify_password(new_password, user.password_hash):
        raise AppError(
            "New password must differ from the current password.",
            code="PASSWORD_UNCHANGED",
            status_code=400,
        )

    now = utcnow()
    user.password_hash = hash_password(new_password)
    user.updated_at = now
    repository.revoke_other_sessions(
        db,
        user_id=user.id,
        except_session_id=current_session_id,
        revoked_at=now,
    )
    audit_service.record_event(
        db,
        action=AuditAction.AUTH_PASSWORD_CHANGED,
        resource_type="user",
        resource_id=user.id,
        actor_user_id=user.id,
    )
    db.commit()
