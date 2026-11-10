from datetime import timedelta
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.permissions import get_user_permissions
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    is_acceptable_password,
    verify_password,
)
from app.core.time import utcnow
from app.models import (
    Organization,
    OrganizationMember,
    RegistrationRequest,
    Role,
    User,
    UserRoleAssignment,
    UserSession,
    UserStatus,
)
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository
from app.modules.auth.schemas import OrganizationSummary, UserResponse

_LAST_SEEN_UPDATE_INTERVAL = timedelta(minutes=5)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def build_user_response(user: User) -> UserResponse:
    """Build a complete UserResponse including roles, permissions, and organizations."""
    roles: list[str] = []
    for assignment in getattr(user, "assigned_roles", []):
        if assignment.role and assignment.role.key not in roles:
            roles.append(assignment.role.key)

    if not roles and getattr(user, "role", None):
        roles.append(str(user.role))

    permissions = [p.value for p in get_user_permissions(user)]

    orgs: list[OrganizationSummary] = []
    for member in getattr(user, "memberships", []):
        if member.organization:
            orgs.append(
                OrganizationSummary(
                    id=member.organization.id,
                    name=member.organization.name,
                    slug=member.organization.slug,
                    role=roles[0] if roles else None,
                )
            )

    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        is_active=user.is_active,
        roles=roles,
        permissions=permissions,
        organizations=orgs,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def register_user(
    db: Session,
    *,
    display_name: str,
    email: str,
    password: str,
    organization_name: str | None = None,
) -> tuple[User, RegistrationRequest]:
    """Public registration. Creates a pending user and registration request."""
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
        name=display_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        status=UserStatus.PENDING.value,
    )
    req = repository.create_registration_request(db, user_id=user.id)

    audit_service.record_event(
        db,
        action=AuditAction.REGISTRATION_SUBMITTED,
        resource_type="registration_request",
        resource_id=req.id,
        actor_user_id=user.id,
        metadata={"email": user.email, "organization_name": organization_name},
    )
    db.commit()
    db.refresh(user)
    db.refresh(req)
    return user, req


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: Any = "viewer",
    organization_id: uuid.UUID | None = None,
    status: str = UserStatus.ACTIVE.value,
    commit: bool = True,
) -> User:
    """Internal user creation (e.g. by administrator)."""
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
        status=status,
    )

    role_key = getattr(role, "value", str(role)).lower()
    repository.assign_role(
        db,
        user_id=user.id,
        role_key=role_key,
        organization_id=organization_id,
    )

    # If platform admin, also ensure platform_admin role is assigned
    if role_key in {"admin", "platform_admin"}:
        repository.assign_role(db, user_id=user.id, role_key="platform_admin")

    if organization_id:
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user.id,
            membership_status="active",
        )
        db.add(member)

    if commit:
        db.commit()
        db.refresh(user)
    else:
        db.flush()
    return user


def create_initial_admin(db: Session, *, name: str, email: str, password: str) -> User:
    repository.ensure_default_roles_and_permissions(db)
    if repository.admin_exists(db):
        raise AppError(
            "An administrator already exists.",
            code="ADMIN_EXISTS",
            status_code=409,
        )
    return create_user(
        db,
        name=name,
        email=email,
        password=password,
        role="admin",
        status=UserStatus.ACTIVE.value,
    )


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = repository.get_user_by_email(db, normalize_email(email))

    if user is None:
        audit_service.record_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            resource_type="auth",
            metadata={"reason": "invalid_credentials"},
        )
        db.commit()
        raise AppError("Invalid email or password.", code="INVALID_CREDENTIALS", status_code=401)

    if not user.password_hash or not verify_password(password, user.password_hash):
        audit_service.record_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            resource_type="auth",
            actor_user_id=user.id,
            metadata={"reason": "invalid_credentials"},
        )
        db.commit()
        raise AppError("Invalid email or password.", code="INVALID_CREDENTIALS", status_code=401)

    if user.status == UserStatus.PENDING.value:
        raise AppError(
            "Account registration is pending administrator approval.",
            code="ACCOUNT_PENDING",
            status_code=403,
        )

    if user.status in {UserStatus.REJECTED.value, UserStatus.SUSPENDED.value}:
        raise AppError(
            "Account is not active.",
            code="ACCOUNT_INACTIVE",
            status_code=403,
        )

    user.last_login_at = utcnow()
    db.commit()
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

    primary_role = "viewer"
    if getattr(user, "assigned_roles", None):
        primary_role = user.assigned_roles[0].role.key

    audit_service.record_event(
        db,
        action=AuditAction.AUTH_LOGIN_SUCCEEDED,
        resource_type="session",
        resource_id=session.id,
        actor_user_id=user.id,
        metadata={"role": primary_role},
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


def revoke_owned_session(db: Session, *, user: User, session_id: uuid.UUID | str) -> None:
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
    current_session_id: uuid.UUID,
) -> None:
    if not user.password_hash or not verify_password(current_password, user.password_hash):
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


def list_pending_registrations(db: Session, limit: int = 50, offset: int = 0) -> list[RegistrationRequest]:
    return repository.list_registration_requests(db, status="pending", limit=limit, offset=offset)


def approve_registration(
    db: Session,
    *,
    admin_user: User,
    request_id: uuid.UUID | str,
    organization_id: uuid.UUID | str | None = None,
    role_key: str = "viewer",
    review_note: str | None = None,
) -> tuple[RegistrationRequest, User]:
    req = repository.get_registration_request_by_id(db, request_id)
    if not req:
        raise AppError("Registration request not found.", code="NOT_FOUND", status_code=404)
    if req.status != "pending":
        raise AppError("Registration request is already reviewed.", code="ALREADY_REVIEWED", status_code=400)

    now = utcnow()
    req.status = "approved"
    req.reviewed_by = admin_user.id
    req.reviewed_at = now
    req.review_note = review_note

    target_user = req.user
    target_user.status = UserStatus.ACTIVE.value
    target_user.updated_at = now

    parsed_org_id = None
    if organization_id:
        parsed_org_id = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        member = OrganizationMember(
            organization_id=parsed_org_id,
            user_id=target_user.id,
            membership_status="active",
        )
        db.add(member)

    repository.assign_role(
        db,
        user_id=target_user.id,
        role_key=role_key,
        organization_id=parsed_org_id,
    )

    audit_service.record_event(
        db,
        action=AuditAction.REGISTRATION_APPROVED,
        resource_type="registration_request",
        resource_id=req.id,
        actor_user_id=admin_user.id,
        metadata={
            "user_id": str(target_user.id),
            "email": target_user.email,
            "role": role_key,
            "organization_id": str(parsed_org_id) if parsed_org_id else None,
            "note": review_note,
        },
    )
    db.commit()
    db.refresh(req)
    db.refresh(target_user)
    return req, target_user


def reject_registration(
    db: Session,
    *,
    admin_user: User,
    request_id: uuid.UUID | str,
    review_note: str | None = None,
) -> RegistrationRequest:
    req = repository.get_registration_request_by_id(db, request_id)
    if not req:
        raise AppError("Registration request not found.", code="NOT_FOUND", status_code=404)
    if req.status != "pending":
        raise AppError("Registration request is already reviewed.", code="ALREADY_REVIEWED", status_code=400)

    now = utcnow()
    req.status = "rejected"
    req.reviewed_by = admin_user.id
    req.reviewed_at = now
    req.review_note = review_note

    target_user = req.user
    target_user.status = UserStatus.REJECTED.value
    target_user.updated_at = now

    audit_service.record_event(
        db,
        action=AuditAction.REGISTRATION_REJECTED,
        resource_type="registration_request",
        resource_id=req.id,
        actor_user_id=admin_user.id,
        metadata={"user_id": str(target_user.id), "email": target_user.email, "note": review_note},
    )
    db.commit()
    db.refresh(req)
    return req
