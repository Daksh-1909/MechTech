from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Organization, OrganizationMember, Role, UserRoleAssignment


def create_organization(
    db: Session,
    *,
    name: str,
    slug: str,
    status: str = "active",
) -> Organization:
    org = Organization(name=name, slug=slug, status=status)
    db.add(org)
    db.flush()
    return org


def get_organization_by_id(db: Session, org_id: uuid.UUID | str) -> Organization | None:
    oid = org_id if isinstance(org_id, uuid.UUID) else uuid.UUID(str(org_id))
    return db.get(Organization, oid)


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.scalar(select(Organization).where(Organization.slug == slug.strip().lower()))


def list_organizations(
    db: Session,
    *,
    user_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Organization]:
    stmt = select(Organization).order_by(Organization.name.asc()).limit(limit).offset(offset)
    if user_id is not None:
        stmt = (
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name.asc())
            .limit(limit)
            .offset(offset)
        )
    return list(db.scalars(stmt))


def add_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str = "active",
) -> OrganizationMember:
    existing = get_member(db, organization_id=organization_id, user_id=user_id)
    if existing:
        return existing
    member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        membership_status=status,
    )
    db.add(member)
    db.flush()
    return member


def get_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> OrganizationMember | None:
    return db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )


def list_members(db: Session, organization_id: uuid.UUID) -> list[OrganizationMember]:
    return list(
        db.scalars(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.joined_at.asc())
        )
    )

