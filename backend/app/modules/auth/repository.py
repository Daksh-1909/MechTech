from datetime import datetime
from typing import Sequence
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.permissions import Permission, ROLE_PERMISSIONS
from app.models import (
    Organization,
    OrganizationMember,
    PermissionModel,
    RegistrationRequest,
    Role,
    RolePermission,
    User,
    UserRoleAssignment,
    UserSession,
    UserStatus,
)


def get_user_by_id(db: Session, user_id: uuid.UUID | str) -> User | None:
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    return db.scalar(
        select(User)
        .options(
            joinedload(User.assigned_roles).joinedload(UserRoleAssignment.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission),
            joinedload(User.memberships).joinedload(OrganizationMember.organization),
        )
        .where(User.id == uid)
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized = email.strip().lower()
    return db.scalar(
        select(User)
        .options(
            joinedload(User.assigned_roles).joinedload(UserRoleAssignment.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission),
            joinedload(User.memberships).joinedload(OrganizationMember.organization),
        )
        .where(User.email == normalized)
    )


def ensure_default_roles_and_permissions(db: Session) -> dict[str, Role]:
    """Seed system roles and granular permissions if they do not exist."""
    existing_perms = {p.key: p for p in db.scalars(select(PermissionModel)).all()}
    for perm_enum in Permission:
        key = perm_enum.value
        if key not in existing_perms:
            perm_obj = PermissionModel(
                key=key,
                description=f"Permission to perform {key.replace('.', ' ')}",
            )
            db.add(perm_obj)
            existing_perms[key] = perm_obj

    db.flush()

    roles_def = [
        ("platform_admin", "Platform Administrator", "platform", "Full platform administrative control"),
        ("org_admin", "Organization Administrator", "organization", "Organization-level administration"),
        ("maintainer", "Maintainer", "organization", "Equipment, monitoring, and maintenance operations"),
        ("viewer", "Viewer", "organization", "Read-only access to equipment and monitoring data"),
        ("demo_user", "Demonstration User", "organization", "Restricted academic demonstration user"),
        # Legacy role aliases
        ("admin", "Admin", "platform", "Platform Administrator"),
        ("technician", "Technician", "organization", "Maintainer"),
        ("operator", "Operator", "organization", "Viewer"),
    ]

    roles_by_key: dict[str, Role] = {}
    for key, name, scope, desc in roles_def:
        role = db.scalar(select(Role).where(Role.key == key))
        if not role:
            role = Role(key=key, name=name, scope=scope, description=desc)
            db.add(role)
            db.flush()

            assigned_perms = ROLE_PERMISSIONS.get(key, set())
            for perm in assigned_perms:
                perm_obj = existing_perms.get(perm.value)
                if perm_obj:
                    rp = RolePermission(role_id=role.id, permission_id=perm_obj.id)
                    db.add(rp)
        roles_by_key[key] = role

    db.flush()
    return roles_by_key


def assign_role(
    db: Session,
    *,
    user_id: uuid.UUID,
    role_key: str,
    organization_id: uuid.UUID | None = None,
) -> UserRoleAssignment:
    roles = ensure_default_roles_and_permissions(db)
    role = roles.get(role_key)
    if not role:
        role = db.scalar(select(Role).where(Role.key == role_key))
        if not role:
            role = Role(key=role_key, name=role_key.title(), scope="organization", description=None)
            db.add(role)
            db.flush()

    existing = db.scalar(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.organization_id == organization_id,
        )
    )
    if existing:
        return existing

    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role.id,
        organization_id=organization_id,
    )
    db.add(assignment)
    db.flush()
    return assignment


def create_user_record(
    db: Session,
    *,
    name: str,
    email: str,
    password_hash: str | None,
    status: str = UserStatus.PENDING.value,
) -> User:
    user = User(
        display_name=name,
        email=email.strip().lower(),
        password_hash=password_hash,
        status=status,
    )
    db.add(user)
    db.flush()
    return user


def create_registration_request(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> RegistrationRequest:
    req = RegistrationRequest(user_id=user_id, status="pending")
    db.add(req)
    db.flush()
    return req


def list_registration_requests(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[RegistrationRequest]:
    stmt = (
        select(RegistrationRequest)
        .options(joinedload(RegistrationRequest.user))
        .order_by(RegistrationRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(RegistrationRequest.status == status)
    return list(db.scalars(stmt))


def get_registration_request_by_id(
    db: Session,
    request_id: uuid.UUID | str,
) -> RegistrationRequest | None:
    rid = request_id if isinstance(request_id, uuid.UUID) else uuid.UUID(str(request_id))
    return db.scalar(
        select(RegistrationRequest)
        .options(joinedload(RegistrationRequest.user))
        .where(RegistrationRequest.id == rid)
    )


def admin_exists(db: Session) -> bool:
    admin_roles = db.scalars(select(Role).where(Role.key.in_(["platform_admin", "admin"]))).all()
    if not admin_roles:
        return False
    role_ids = [r.id for r in admin_roles]
    count = db.scalar(
        select(func.count())
        .select_from(UserRoleAssignment)
        .join(User, UserRoleAssignment.user_id == User.id)
        .where(
            UserRoleAssignment.role_id.in_(role_ids),
            User.status == UserStatus.ACTIVE.value,
        )
    )
    return bool(count)


def create_session_record(
    db: Session,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    csrf_token_hash: str,
    expires_at: datetime,
    user_agent_summary: str | None,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token_hash=csrf_token_hash,
        expires_at=expires_at,
        user_agent_summary=user_agent_summary,
    )
    db.add(session)
    db.flush()
    return session


def get_session_by_token_hash(db: Session, token_hash: str) -> UserSession | None:
    return db.scalar(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.token_hash == token_hash)
    )


def list_sessions_for_user(db: Session, user_id: uuid.UUID | str) -> list[UserSession]:
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    return list(
        db.scalars(
            select(UserSession)
            .where(UserSession.user_id == uid)
            .order_by(UserSession.created_at.desc())
        )
    )


def get_session_for_user(
    db: Session,
    *,
    session_id: uuid.UUID | str,
    user_id: uuid.UUID | str,
) -> UserSession | None:
    sid = session_id if isinstance(session_id, uuid.UUID) else uuid.UUID(str(session_id))
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    return db.scalar(
        select(UserSession).where(
            UserSession.id == sid,
            UserSession.user_id == uid,
        )
    )


def revoke_other_sessions(
    db: Session,
    *,
    user_id: uuid.UUID,
    except_session_id: uuid.UUID,
    revoked_at: datetime,
) -> None:
    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.id != except_session_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )


def revoke_all_sessions(
    db: Session,
    *,
    user_id: uuid.UUID,
    revoked_at: datetime,
) -> None:
    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )
