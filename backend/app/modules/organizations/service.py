import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import Organization, OrganizationMember, Role, User, UserRoleAssignment
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository as auth_repo
from app.modules.organizations import repository
from app.modules.organizations.schemas import OrganizationMemberResponse


def create_organization(
    db: Session,
    *,
    actor: User,
    name: str,
    slug: str,
) -> Organization:
    existing = repository.get_organization_by_slug(db, slug)
    if existing:
        raise AppError("An organization with this slug already exists.", code="SLUG_IN_USE", status_code=409)

    org = repository.create_organization(db, name=name.strip(), slug=slug.strip().lower())

    # Add creator as org_admin
    repository.add_member(db, organization_id=org.id, user_id=actor.id, status="active")
    auth_repo.assign_role(db, user_id=actor.id, role_key="org_admin", organization_id=org.id)

    audit_service.record_event(
        db,
        action=AuditAction.ORGANIZATION_CREATED,
        resource_type="organization",
        resource_id=org.id,
        actor_user_id=actor.id,
        organization_id=org.id,
        metadata={"name": org.name, "slug": org.slug},
    )
    db.commit()
    db.refresh(org)
    return org


def list_organizations(
    db: Session,
    *,
    actor: User,
    limit: int = 50,
    offset: int = 0,
) -> list[Organization]:
    # If platform admin, list all organizations
    is_platform_admin = any(
        a.role and a.role.key == "platform_admin"
        for a in getattr(actor, "assigned_roles", [])
    )
    if is_platform_admin:
        return repository.list_organizations(db, limit=limit, offset=offset)

    return repository.list_organizations(db, user_id=actor.id, limit=limit, offset=offset)


def get_organization(
    db: Session,
    *,
    actor: User,
    org_id: uuid.UUID | str,
) -> Organization:
    oid = org_id if isinstance(org_id, uuid.UUID) else uuid.UUID(str(org_id))
    org = repository.get_organization_by_id(db, oid)
    if not org:
        raise AppError("Organization not found.", code="NOT_FOUND", status_code=404)

    is_platform_admin = any(
        a.role and a.role.key == "platform_admin"
        for a in getattr(actor, "assigned_roles", [])
    )
    if not is_platform_admin:
        membership = repository.get_member(db, organization_id=oid, user_id=actor.id)
        if not membership:
            raise AppError("Access denied to this organization.", code="FORBIDDEN", status_code=403)

    return org


def add_member(
    db: Session,
    *,
    actor: User,
    org_id: uuid.UUID | str,
    user_id: uuid.UUID | str,
    role_key: str = "viewer",
) -> OrganizationMember:
    oid = org_id if isinstance(org_id, uuid.UUID) else uuid.UUID(str(org_id))
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))

    org = get_organization(db, actor=actor, org_id=oid)

    # Check permission to manage organization
    is_platform_admin = any(
        a.role and a.role.key == "platform_admin"
        for a in getattr(actor, "assigned_roles", [])
    )
    if not is_platform_admin and not has_permission(actor, Permission.ORGANIZATION_MANAGE, organization_id=oid):
        raise AppError("You do not have permission to manage members in this organization.", code="FORBIDDEN", status_code=403)

    target_user = auth_repo.get_user_by_id(db, uid)
    if not target_user:
        raise AppError("User not found.", code="NOT_FOUND", status_code=404)

    member = repository.add_member(db, organization_id=oid, user_id=uid)
    auth_repo.assign_role(db, user_id=uid, role_key=role_key, organization_id=oid)

    audit_service.record_event(
        db,
        action=AuditAction.ORGANIZATION_MEMBER_ADDED,
        resource_type="organization_member",
        resource_id=member.id,
        actor_user_id=actor.id,
        organization_id=oid,
        metadata={"user_id": str(uid), "role": role_key},
    )
    db.commit()
    db.refresh(member)
    return member


def list_members(
    db: Session,
    *,
    actor: User,
    org_id: uuid.UUID | str,
) -> list[OrganizationMemberResponse]:
    oid = org_id if isinstance(org_id, uuid.UUID) else uuid.UUID(str(org_id))
    org = get_organization(db, actor=actor, org_id=oid)

    members = repository.list_members(db, oid)

    # Get user role assignments in this org
    role_assignments = db.scalars(
        select(UserRoleAssignment)
        .join(Role)
        .where(UserRoleAssignment.organization_id == oid)
    ).all()
    user_role_map = {ra.user_id: ra.role.key for ra in role_assignments if ra.role}

    return [
        OrganizationMemberResponse(
            id=m.id,
            user_id=m.user_id,
            display_name=m.user.display_name,
            email=m.user.email,
            membership_status=m.membership_status,
            joined_at=m.joined_at,
            role=user_role_map.get(m.user_id, "viewer"),
        )
        for m in members
    ]

