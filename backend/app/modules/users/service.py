from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.core.time import utcnow
from app.models import User, UserRole
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository as auth_repository
from app.modules.auth import service as auth_service
from app.modules.users import repository


def list_users(db: Session, *, limit: int, offset: int) -> list[User]:
    return repository.list_users(db, limit=limit, offset=offset)


def get_user(db: Session, user_id: int) -> User:
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
    role: UserRole,
) -> User:
    user = auth_service.create_user(
        db,
        name=name,
        email=email,
        password=password,
        role=role,
        commit=False,
    )
    audit_service.record_event(
        db,
        action=AuditAction.USER_CREATED,
        resource_type="user",
        resource_id=user.id,
        actor_user_id=actor.id,
        metadata={"role": user.role},
    )
    db.commit()
    db.refresh(user)
    return user


def _ensure_can_manage_target(actor: User, target: User, *, changing_role: bool) -> None:
    if has_permission(actor, Permission.USERS_MANAGE):
        if changing_role and actor.id == target.id:
            raise AppError(
                "You cannot change your own role.",
                code="SELF_ROLE_CHANGE",
                status_code=403,
            )
        return

    if actor.id != target.id:
        raise AppError(
            "You do not have permission to perform this action.",
            code="FORBIDDEN",
            status_code=403,
        )

    if changing_role:
        raise AppError(
            "You cannot change your own role.",
            code="SELF_ROLE_CHANGE",
            status_code=403,
        )


def update_user(
    db: Session,
    *,
    actor: User,
    user_id: int,
    changes: dict[str, Any],
) -> User:
    if not has_permission(actor, Permission.USERS_MANAGE) and actor.id != user_id:
        raise AppError(
            "You do not have permission to perform this action.",
            code="FORBIDDEN",
            status_code=403,
        )

    target = get_user(db, user_id)
    _ensure_can_manage_target(actor, target, changing_role="role" in changes)

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

    if "name" in changes:
        target.name = str(changes["name"])
        updated_fields.append("name")

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
        new_role = UserRole(changes["role"])
        if new_role.value != target.role:
            target.role = new_role.value
            updated_fields.append("role")
            auth_repository.revoke_all_sessions(
                db,
                user_id=target.id,
                revoked_at=utcnow(),
            )
            audit_service.record_event(
                db,
                action=AuditAction.USER_ROLE_CHANGED,
                resource_type="user",
                resource_id=target.id,
                actor_user_id=actor.id,
                metadata={"role": new_role.value},
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
    user_id: int,
    is_active: bool,
) -> User:
    target = get_user(db, user_id)

    if actor.id == target.id and not is_active:
        raise AppError(
            "You cannot deactivate your own account.",
            code="SELF_DEACTIVATION",
            status_code=400,
        )

    if target.is_active == is_active:
        return target

    target.is_active = is_active
    target.updated_at = utcnow()

    if not is_active:
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
        metadata={"is_active": is_active},
    )
    db.commit()
    db.refresh(target)
    return target
