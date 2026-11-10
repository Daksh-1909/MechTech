from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import (
    Component,
    Equipment,
    EquipmentAssignment,
    EquipmentType,
    User,
)
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import repository as auth_repo
from app.modules.equipment import repository
from app.modules.equipment.schemas import EquipmentResponse, EquipmentTypeResponse
from app.modules.organizations import repository as org_repo


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def resolve_organization_for_actor(actor: User, requested_org_id: uuid.UUID | str | None = None) -> uuid.UUID:
    """Resolve and validate the active organization ID for an action."""
    if requested_org_id is not None:
        oid = requested_org_id if isinstance(requested_org_id, uuid.UUID) else uuid.UUID(str(requested_org_id))
        if _is_platform_admin(actor):
            return oid
        # Verify membership
        memberships = getattr(actor, "memberships", [])
        if any(m.organization_id == oid for m in memberships):
            return oid
        raise AppError("You do not have access to this organization.", code="FORBIDDEN", status_code=403)

    # If not requested, pick user's first membership
    memberships = getattr(actor, "memberships", [])
    if memberships:
        return memberships[0].organization_id

    # If platform admin without membership, get or create demo org
    if _is_platform_admin(actor):
        demo_org = org_repo.get_organization_by_slug(None, "academic-demonstration")  # type: ignore[arg-type]
        if demo_org:
            return demo_org.id

    raise AppError("No organization membership found for user.", code="NO_ORGANIZATION", status_code=400)


def build_equipment_response(equipment: Equipment) -> EquipmentResponse:
    spec = equipment.specification.specification if equipment.specification else None
    comp_count = len(getattr(equipment, "components", []))
    sens_count = len(getattr(equipment, "sensors", []))

    return EquipmentResponse(
        id=equipment.id,
        organization_id=equipment.organization_id,
        equipment_type_id=equipment.equipment_type_id,
        equipment_type_key=equipment.equipment_type.key if equipment.equipment_type else "electric_motor",
        asset_tag=equipment.asset_tag,
        name=equipment.name,
        manufacturer=equipment.manufacturer,
        model_number=equipment.model_number,
        serial_number=equipment.serial_number,
        location_label=equipment.location_label,
        installation_date=equipment.installation_date,
        status=equipment.status,
        specification=spec,
        components_count=comp_count,
        sensors_count=sens_count,
        created_at=equipment.created_at,
        updated_at=equipment.updated_at,
    )


def create_equipment(
    db: Session,
    *,
    actor: User,
    values: dict[str, Any],
) -> Equipment:
    org_id = resolve_organization_for_actor(actor, values.get("organization_id"))

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_CREATE, organization_id=org_id):
        raise AppError("Permission denied to create equipment in this organization.", code="FORBIDDEN", status_code=403)

    eq_types = repository.ensure_default_equipment_types(db)
    type_key = values.get("equipment_type_key") or values.get("category") or "electric_motor"
    eq_type = eq_types.get(type_key) or repository.get_equipment_type_by_key(db, type_key)
    if not eq_type:
        eq_type = eq_types.get("electric_motor")

    if not eq_type:
        raise AppError(f"Equipment type '{type_key}' not found.", code="TYPE_NOT_FOUND", status_code=400)

    asset_tag = values.get("asset_tag")
    if asset_tag:
        existing = db.query(Equipment).filter_by(organization_id=org_id, asset_tag=asset_tag).first()
        if existing:
            raise AppError("An asset with this tag already exists in the organization.", code="ASSET_TAG_IN_USE", status_code=409)

    equipment = repository.create_equipment(
        db,
        organization_id=org_id,
        equipment_type_id=eq_type.id,
        name=values["name"],
        created_by=actor.id,
        asset_tag=asset_tag,
        manufacturer=values.get("manufacturer"),
        model_number=values.get("model_number"),
        serial_number=values.get("serial_number"),
        location_label=values.get("location_label") or values.get("location"),
        installation_date=values.get("installation_date"),
        status=values.get("status", "operational"),
        specification=values.get("specification"),
    )

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_CREATED,
        resource_type="equipment",
        resource_id=equipment.id,
        actor_user_id=actor.id,
        organization_id=org_id,
        metadata={"name": equipment.name, "type": eq_type.key},
    )
    db.commit()
    db.refresh(equipment)
    return equipment


def get_equipment(db: Session, actor: User, equipment_id: uuid.UUID | str) -> Equipment:
    equipment = repository.get_equipment_by_id(db, equipment_id)
    if not equipment:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == equipment.organization_id for m in memberships):
            raise AppError("Access denied to this equipment.", code="FORBIDDEN", status_code=403)

    return equipment


def list_equipment(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Equipment]:
    org_id = None
    if organization_id:
        org_id = resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            org_id = memberships[0].organization_id

    return repository.list_equipment(
        db,
        organization_id=org_id,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


def update_equipment(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Equipment:
    equipment = get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to update equipment.", code="FORBIDDEN", status_code=403)

    if "location" in changes and "location_label" not in changes:
        changes["location_label"] = changes.pop("location")

    updated = repository.update_equipment(db, equipment_id=equipment.id, changes=changes)
    if not updated:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_UPDATED,
        resource_type="equipment",
        resource_id=updated.id,
        actor_user_id=actor.id,
        organization_id=updated.organization_id,
        metadata={"changes": list(changes.keys())},
    )
    db.commit()
    db.refresh(updated)
    return updated


def archive_equipment(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
) -> Equipment:
    equipment = get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_ARCHIVE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to archive equipment.", code="FORBIDDEN", status_code=403)

    archived = repository.archive_equipment(db, equipment.id)
    if not archived:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_ARCHIVED,
        resource_type="equipment",
        resource_id=archived.id,
        actor_user_id=actor.id,
        organization_id=archived.organization_id,
    )
    db.commit()
    db.refresh(archived)
    return archived


def create_component(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    component_key: str,
    name: str,
    component_type: str = "component",
    parent_component_id: uuid.UUID | None = None,
    manufacturer: str | None = None,
    model_number: str | None = None,
    serial_number: str | None = None,
    description: str | None = None,
) -> Component:
    equipment = get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to add components to this equipment.", code="FORBIDDEN", status_code=403)

    # Check parent component if provided
    if parent_component_id:
        parent = repository.get_component_by_id(db, parent_component_id)
        if not parent or parent.equipment_id != equipment.id:
            raise AppError("Parent component must belong to the same equipment.", code="INVALID_PARENT_COMPONENT", status_code=400)

    # Check key uniqueness within equipment
    existing = repository.get_component_by_key(db, equipment_id=equipment.id, component_key=component_key)
    if existing:
        raise AppError(f"Component key '{component_key}' already exists for this equipment.", code="COMPONENT_KEY_IN_USE", status_code=409)

    component = repository.create_component(
        db,
        organization_id=equipment.organization_id,
        equipment_id=equipment.id,
        component_key=component_key,
        name=name,
        component_type=component_type,
        parent_component_id=parent_component_id,
        manufacturer=manufacturer,
        model_number=model_number,
        serial_number=serial_number,
        description=description,
    )

    audit_service.record_event(
        db,
        action=AuditAction.COMPONENT_CREATED,
        resource_type="component",
        resource_id=component.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"component_key": component.component_key, "equipment_id": str(equipment.id)},
    )
    db.commit()
    db.refresh(component)
    return component


def list_components(db: Session, actor: User, equipment_id: uuid.UUID | str) -> list[Component]:
    equipment = get_equipment(db, actor, equipment_id)
    return repository.list_components(db, equipment.id)


def update_component(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    component_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Component:
    equipment = get_equipment(db, actor, equipment_id)
    comp = repository.get_component_by_id(db, component_id)
    if not comp or comp.equipment_id != equipment.id:
        raise AppError("Component not found on this equipment.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to update components.", code="FORBIDDEN", status_code=403)

    if "parent_component_id" in changes and changes["parent_component_id"]:
        parent = repository.get_component_by_id(db, changes["parent_component_id"])
        if not parent or parent.equipment_id != equipment.id:
            raise AppError("Parent component must belong to the same equipment.", code="INVALID_PARENT_COMPONENT", status_code=400)

    updated = repository.update_component(db, comp.id, changes)
    if not updated:
        raise AppError("Component not found.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.COMPONENT_UPDATED,
        resource_type="component",
        resource_id=updated.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"changes": list(changes.keys())},
    )
    db.commit()
    db.refresh(updated)
    return updated


def assign_equipment(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    user_id: uuid.UUID | str,
    assignment_type: str = "primary_maintainer",
) -> EquipmentAssignment:
    equipment = get_equipment(db, actor, equipment_id)
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))

    target_user = auth_repo.get_user_by_id(db, uid)
    if not target_user:
        raise AppError("User not found.", code="NOT_FOUND", status_code=404)

    # Check target user belongs to same organization
    memberships = getattr(target_user, "memberships", [])
    if not any(m.organization_id == equipment.organization_id for m in memberships):
        raise AppError("Target user must belong to the same organization.", code="INVALID_USER_ORGANIZATION", status_code=400)

    assignment = repository.create_assignment(
        db,
        equipment_id=equipment.id,
        user_id=uid,
        assigned_by=actor.id,
        assignment_type=assignment_type,
    )
    db.commit()
    db.refresh(assignment)
    return assignment
