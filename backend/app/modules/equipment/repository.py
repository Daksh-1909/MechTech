from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models import (
    Component,
    Equipment,
    EquipmentAssignment,
    EquipmentSpecification,
    EquipmentType,
    Sensor,
)


def ensure_default_equipment_types(db: Session) -> dict[str, EquipmentType]:
    default_types = [
        ("electric_motor", "Electric Motor", "1.0", True),
    ]
    types_by_key: dict[str, EquipmentType] = {}
    for key, name, version, enabled in default_types:
        eq_type = db.scalar(select(EquipmentType).where(EquipmentType.key == key))
        if not eq_type:
            eq_type = EquipmentType(
                key=key,
                name=name,
                schema_version=version,
                is_enabled=enabled,
            )
            db.add(eq_type)
            db.flush()
        types_by_key[key] = eq_type
    db.flush()
    return types_by_key


def get_equipment_type_by_key(db: Session, key: str) -> EquipmentType | None:
    return db.scalar(select(EquipmentType).where(EquipmentType.key == key))


def list_equipment_types(db: Session) -> list[EquipmentType]:
    ensure_default_equipment_types(db)
    return list(db.scalars(select(EquipmentType).where(EquipmentType.is_enabled.is_(True)).order_by(EquipmentType.name.asc())))


def create_equipment_type(
    db: Session,
    *,
    key: str,
    name: str,
    schema_version: str = "1.0",
) -> EquipmentType:
    eq_type = EquipmentType(
        key=key.strip().lower(),
        name=name.strip(),
        schema_version=schema_version,
        is_enabled=True,
    )
    db.add(eq_type)
    db.flush()
    return eq_type


def create_equipment(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_type_id: uuid.UUID,
    name: str,
    created_by: uuid.UUID,
    asset_tag: str | None = None,
    manufacturer: str | None = None,
    model_number: str | None = None,
    serial_number: str | None = None,
    location_label: str | None = None,
    installation_date: datetime | None = None,
    status: str = "operational",
    specification: dict[str, Any] | None = None,
) -> Equipment:
    eq = Equipment(
        organization_id=organization_id,
        equipment_type_id=equipment_type_id,
        asset_tag=asset_tag,
        name=name,
        manufacturer=manufacturer,
        model_number=model_number,
        serial_number=serial_number,
        location_label=location_label,
        installation_date=installation_date,
        status=status,
        created_by=created_by,
    )
    db.add(eq)
    db.flush()

    if specification is not None:
        spec = EquipmentSpecification(
            equipment_id=eq.id,
            schema_version="1.0",
            specification=specification,
        )
        db.add(spec)
        db.flush()

    return eq


def get_equipment_by_id(db: Session, equipment_id: uuid.UUID | str) -> Equipment | None:
    eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
    return db.scalar(
        select(Equipment)
        .options(
            joinedload(Equipment.equipment_type),
            joinedload(Equipment.specification),
            joinedload(Equipment.organization),
        )
        .where(Equipment.id == eid)
    )


def list_equipment(
    db: Session,
    *,
    organization_id: uuid.UUID | None = None,
    equipment_type_id: uuid.UUID | None = None,
    status: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Equipment]:
    stmt = (
        select(Equipment)
        .options(
            joinedload(Equipment.equipment_type),
            joinedload(Equipment.specification),
        )
        .order_by(Equipment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if organization_id is not None:
        stmt = stmt.where(Equipment.organization_id == organization_id)
    if equipment_type_id is not None:
        stmt = stmt.where(Equipment.equipment_type_id == equipment_type_id)
    if status is not None:
        stmt = stmt.where(Equipment.status == status)
    elif not include_archived:
        stmt = stmt.where(Equipment.status != "archived")

    return list(db.scalars(stmt))


def update_equipment(
    db: Session,
    *,
    equipment_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Equipment | None:
    eq = get_equipment_by_id(db, equipment_id)
    if not eq:
        return None

    spec_changes = changes.pop("specification", None)

    for field, value in changes.items():
        if hasattr(eq, field) and field not in {"id", "created_at", "organization_id", "created_by"}:
            setattr(eq, field, value)

    if spec_changes is not None:
        if eq.specification:
            eq.specification.specification.update(spec_changes)
            eq.specification.updated_at = utcnow()
        else:
            spec = EquipmentSpecification(
                equipment_id=eq.id,
                schema_version="1.0",
                specification=spec_changes,
            )
            db.add(spec)

    eq.updated_at = utcnow()
    db.flush()
    return eq


def archive_equipment(db: Session, equipment_id: uuid.UUID | str) -> Equipment | None:
    eq = get_equipment_by_id(db, equipment_id)
    if not eq:
        return None
    eq.status = "archived"
    eq.updated_at = utcnow()
    db.flush()
    return eq


def create_component(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    component_key: str,
    name: str,
    component_type: str = "component",
    parent_component_id: uuid.UUID | None = None,
    manufacturer: str | None = None,
    model_number: str | None = None,
    serial_number: str | None = None,
    description: str | None = None,
) -> Component:
    comp = Component(
        organization_id=organization_id,
        equipment_id=equipment_id,
        parent_component_id=parent_component_id,
        component_key=component_key,
        component_type=component_type,
        name=name,
        manufacturer=manufacturer,
        model_number=model_number,
        serial_number=serial_number,
        description=description,
        status="operational",
    )
    db.add(comp)
    db.flush()
    return comp


def get_component_by_id(db: Session, component_id: uuid.UUID | str) -> Component | None:
    cid = component_id if isinstance(component_id, uuid.UUID) else uuid.UUID(str(component_id))
    return db.get(Component, cid)


def get_component_by_key(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    component_key: str,
) -> Component | None:
    return db.scalar(
        select(Component).where(
            Component.equipment_id == equipment_id,
            Component.component_key == component_key,
        )
    )


def list_components(db: Session, equipment_id: uuid.UUID | str) -> list[Component]:
    eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
    return list(
        db.scalars(
            select(Component)
            .where(Component.equipment_id == eid)
            .order_by(Component.component_key.asc())
        )
    )


def update_component(
    db: Session,
    component_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Component | None:
    cid = component_id if isinstance(component_id, uuid.UUID) else uuid.UUID(str(component_id))
    comp = db.get(Component, cid)
    if not comp:
        return None
    for field, value in changes.items():
        if hasattr(comp, field) and field not in {"id", "equipment_id", "organization_id", "created_at"}:
            setattr(comp, field, value)
    comp.updated_at = utcnow()
    db.flush()
    return comp


def create_assignment(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    user_id: uuid.UUID,
    assigned_by: uuid.UUID,
    assignment_type: str = "primary_maintainer",
) -> EquipmentAssignment:
    assignment = EquipmentAssignment(
        equipment_id=equipment_id,
        user_id=user_id,
        assigned_by=assigned_by,
        assignment_type=assignment_type,
    )
    db.add(assignment)
    db.flush()
    return assignment


def list_assignments(db: Session, equipment_id: uuid.UUID | str) -> list[EquipmentAssignment]:
    eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
    return list(
        db.scalars(
            select(EquipmentAssignment)
            .where(EquipmentAssignment.equipment_id == eid)
            .order_by(EquipmentAssignment.assigned_at.desc())
        )
    )
