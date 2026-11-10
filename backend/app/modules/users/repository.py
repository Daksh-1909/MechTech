import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import OrganizationMember, Role, RolePermission, User, UserRoleAssignment


def list_users(db: Session, *, limit: int, offset: int) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .options(
                joinedload(User.assigned_roles).joinedload(UserRoleAssignment.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission),
                joinedload(User.memberships).joinedload(OrganizationMember.organization),
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
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
