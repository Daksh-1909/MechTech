from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.models import Component, Equipment, User
from app.models.enums import EquipmentStatus
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository

_OPTIONAL_FIELDS = (
    "manufacturer",
    "model_number",
    "serial_number",
    "location",
    "description",
)


def get_equipment(db: Session, equipment_id: str) -> Equipment:
    equipment = repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return equipment


def list_equipment(db: Session, *, include_archived: bool) -> list[Equipment]:
    return repository.list_equipment(db, include_archived=include_archived)


def create_equipment(
    db: Session,
    *,
    actor: User,
    values: dict,
) -> Equipment:
    equipment_id = values.pop("id", None) or f"motor-{uuid4().hex[:8]}"
    values.pop("id", None)

    if repository.get_equipment(db, equipment_id) is not None:
        raise AppError(
            "Equipment with this identifier already exists.",
            code="EQUIPMENT_EXISTS",
            status_code=409,
        )

    status = values.get("status", EquipmentStatus.ACTIVE)
    equipment = Equipment(id=equipment_id, **values)
    equipment.status = getattr(status, "value", status)
    db.add(equipment)
    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_CREATED,
        resource_type="equipment",
        resource_id=equipment_id,
        actor_user_id=actor.id,
        metadata={"category": equipment.category, "status": equipment.status},
    )
    db.commit()
    db.refresh(equipment)
    return equipment


def update_equipment(
    db: Session,
    *,
    actor: User,
    equipment_id: str,
    changes: dict,
) -> Equipment:
    equipment = get_equipment(db, equipment_id)

    for required_field in ("name", "category", "status"):
        if required_field in changes and changes[required_field] is None:
            raise AppError(
                "A required field cannot be set to null.",
                code="VALIDATION_ERROR",
                status_code=400,
                details=[{"field": required_field, "issue": "Must not be null."}],
            )

    updated_fields: list[str] = []
    for field, value in changes.items():
        if field == "status" and value is not None:
            value = getattr(value, "value", value)
        if field in _OPTIONAL_FIELDS or field in {"name", "category", "status"}:
            setattr(equipment, field, value)
            updated_fields.append(field)

    if updated_fields:
        equipment.updated_at = utcnow()
        audit_service.record_event(
            db,
            action=AuditAction.EQUIPMENT_UPDATED,
            resource_type="equipment",
            resource_id=equipment.id,
            actor_user_id=actor.id,
            metadata={"fields": updated_fields},
        )
        db.commit()
        db.refresh(equipment)
    return equipment


def archive_equipment(db: Session, *, actor: User, equipment_id: str) -> Equipment:
    equipment = get_equipment(db, equipment_id)
    if equipment.status == EquipmentStatus.ARCHIVED.value:
        return equipment

    equipment.status = EquipmentStatus.ARCHIVED.value
    equipment.updated_at = utcnow()
    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_ARCHIVED,
        resource_type="equipment",
        resource_id=equipment.id,
        actor_user_id=actor.id,
    )
    db.commit()
    db.refresh(equipment)
    return equipment


def list_components(db: Session, *, equipment_id: str) -> list[Component]:
    get_equipment(db, equipment_id)
    return repository.list_components(db, equipment_id)


def create_component(
    db: Session,
    *,
    actor: User,
    equipment_id: str,
    component_key: str,
    name: str,
    description: str | None,
) -> Component:
    equipment = get_equipment(db, equipment_id)
    if equipment.is_archived:
        raise AppError(
            "Archived equipment cannot be modified.",
            code="EQUIPMENT_ARCHIVED",
            status_code=409,
        )

    if (
        repository.get_component_by_key(
            db,
            equipment_id=equipment_id,
            component_key=component_key,
        )
        is not None
    ):
        raise AppError(
            "A component with this key already exists.",
            code="COMPONENT_EXISTS",
            status_code=409,
        )

    component = Component(
        equipment_id=equipment_id,
        component_key=component_key,
        name=name,
        description=description,
    )
    db.add(component)
    db.flush()
    audit_service.record_event(
        db,
        action=AuditAction.COMPONENT_CREATED,
        resource_type="component",
        resource_id=component.id,
        actor_user_id=actor.id,
        metadata={"equipment_id": equipment_id, "component_key": component_key},
    )
    db.commit()
    db.refresh(component)
    return component


def get_component(db: Session, *, equipment_id: str, component_id: int) -> Component:
    component = repository.get_component(db, component_id)
    if component is None or component.equipment_id != equipment_id:
        raise AppError("Component not found.", code="NOT_FOUND", status_code=404)
    return component


def update_component(
    db: Session,
    *,
    actor: User,
    equipment_id: str,
    component_id: int,
    changes: dict,
) -> Component:
    component = get_component(db, equipment_id=equipment_id, component_id=component_id)

    if "name" in changes and changes["name"] is None:
        raise AppError(
            "Name cannot be set to null.",
            code="VALIDATION_ERROR",
            status_code=400,
        )

    updated_fields: list[str] = []
    for field in ("name", "description"):
        if field in changes:
            setattr(component, field, changes[field])
            updated_fields.append(field)

    if updated_fields:
        audit_service.record_event(
            db,
            action=AuditAction.COMPONENT_UPDATED,
            resource_type="component",
            resource_id=component.id,
            actor_user_id=actor.id,
            metadata={"equipment_id": equipment_id, "fields": updated_fields},
        )
        db.commit()
        db.refresh(component)
    return component
