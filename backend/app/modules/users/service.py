from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.core.time import utcnow
from app.models import User, UserStatus
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository as auth_repository
from app.modules.auth import service as auth_service
from app.modules.users import repository


def list_users(db: Session, *, limit: int, offset: int) -> list[User]:
    return repository.list_users(db, limit=limit, offset=offset)


def get_user(db: Session, user_id: uuid.UUID | str) -> User:
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        raise AppError("User not found.", code="NOT_FOUND", status_code=404)
    return user


def create_user(
    db: Session,
    *,
    actor: User,
    name: str,
    email: str,
    password: str,
    role: str = "viewer",
    organization_id: uuid.UUID | None = None,
) -> User:
    user = auth_service.create_user(
        db,
        name=name,
        email=email,
        password=password,
        role=role,
        organization_id=organization_id,
        commit=False,
    )
    audit_service.record_event(
        db,
        action=AuditAction.USER_CREATED,
        resource_type="user",
        resource_id=user.id,
        actor_user_id=actor.id,
        metadata={"role": role},
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    *,
    actor: User,
    user_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> User:
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    if not has_permission(actor, Permission.USER_CREATE) and actor.id != uid:
        raise AppError(
            "You do not have permission to perform this action.",
            code="FORBIDDEN",
            status_code=403,
        )

    target = get_user(db, uid)

    if not changes:
        return target

    for field, value in changes.items():
        if value is None:
            raise AppError(
                "A field cannot be set to null.",
                code="VALIDATION_ERROR",
                status_code=400,
                details=[{"field": field, "issue": "Must not be null."}],
            )

    updated_fields: list[str] = []

    if "name" in changes or "display_name" in changes:
        new_name = str(changes.get("display_name") or changes.get("name"))
        target.display_name = new_name
        updated_fields.append("display_name")

    if "email" in changes:
        normalized_email = auth_service.normalize_email(str(changes["email"]))
        existing = repository.get_user_by_email(db, normalized_email)
        if existing is not None and existing.id != target.id:
            raise AppError(
                "A user with this email already exists.",
                code="EMAIL_IN_USE",
                status_code=409,
            )
        target.email = normalized_email
        updated_fields.append("email")

    if "role" in changes:
        if actor.id == target.id:
            raise AppError("You cannot change your own role.", code="SELF_ROLE_CHANGE", status_code=403)
        if not has_permission(actor, Permission.USER_CREATE):
            raise AppError("Permission denied.", code="FORBIDDEN", status_code=403)

        role_key = str(changes["role"]).lower()
        auth_repository.assign_role(db, user_id=target.id, role_key=role_key)
        auth_repository.revoke_all_sessions(db, user_id=target.id, revoked_at=utcnow())
        updated_fields.append("role")
        audit_service.record_event(
            db,
            action=AuditAction.USER_ROLE_CHANGED,
            resource_type="user",
            resource_id=target.id,
            actor_user_id=actor.id,
            metadata={"role": role_key},
        )

    if updated_fields:
        target.updated_at = utcnow()
        audit_service.record_event(
            db,
            action=AuditAction.USER_UPDATED,
            resource_type="user",
            resource_id=target.id,
            actor_user_id=actor.id,
            metadata={"fields": updated_fields},
        )

    db.commit()
    db.refresh(target)
    return target


def set_user_status(
    db: Session,
    *,
    actor: User,
    user_id: uuid.UUID | str,
    status: str,
) -> User:
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    target = get_user(db, uid)

    if actor.id == target.id and status != UserStatus.ACTIVE.value:
        raise AppError(
            "You cannot deactivate or suspend your own account.",
            code="SELF_DEACTIVATION",
            status_code=400,
        )

    if target.status == status:
        return target

    target.status = status
    target.updated_at = utcnow()

    if status != UserStatus.ACTIVE.value:
        auth_repository.revoke_all_sessions(
            db,
            user_id=target.id,
            revoked_at=utcnow(),
        )

    audit_service.record_event(
        db,
        action=AuditAction.USER_STATUS_CHANGED,
        resource_type="user",
        resource_id=target.id,
        actor_user_id=actor.id,
        metadata={"status": status},
    )
    db.commit()
    db.refresh(target)
    return target
