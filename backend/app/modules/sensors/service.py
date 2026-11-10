from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import Sensor, User
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository as eq_repo
from app.modules.equipment import service as eq_service
from app.modules.sensors import repository


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def create_sensor(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    sensor_key: str,
    measurement_type: str,
    unit: str,
    component_id: uuid.UUID | str | None = None,
    status: str = "active",
    configuration: dict[str, Any] | None = None,
) -> Sensor:
    equipment = eq_service.get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to register sensors on this equipment.", code="FORBIDDEN", status_code=403)

    cid: uuid.UUID | None = None
    if component_id:
        cid = component_id if isinstance(component_id, uuid.UUID) else uuid.UUID(str(component_id))
        comp = eq_repo.get_component_by_id(db, cid)
        if not comp or comp.equipment_id != equipment.id:
            raise AppError("Referenced component must belong to the same equipment.", code="INVALID_COMPONENT", status_code=400)

    existing = repository.get_sensor_by_key(db, equipment_id=equipment.id, sensor_key=sensor_key)
    if existing:
        raise AppError(f"Sensor key '{sensor_key}' already exists for this equipment.", code="SENSOR_KEY_IN_USE", status_code=409)

    sensor = repository.create_sensor(
        db,
        organization_id=equipment.organization_id,
        equipment_id=equipment.id,
        component_id=cid,
        sensor_key=sensor_key,
        measurement_type=measurement_type,
        unit=unit,
        status=status,
        configuration=configuration,
    )

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_UPDATED,
        resource_type="sensor",
        resource_id=sensor.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"sensor_key": sensor.sensor_key, "equipment_id": str(equipment.id), "type": measurement_type},
    )
    db.commit()
    db.refresh(sensor)
    return sensor


def get_sensor(db: Session, actor: User, sensor_id: uuid.UUID | str) -> Sensor:
    sensor = repository.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise AppError("Sensor not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == sensor.organization_id for m in memberships):
            raise AppError("Access denied to this sensor.", code="FORBIDDEN", status_code=403)

    return sensor


def list_sensors(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str | None = None,
    organization_id: uuid.UUID | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Sensor]:
    org_id = None
    if organization_id:
        org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            org_id = memberships[0].organization_id

    eid = None
    if equipment_id:
        eq = eq_service.get_equipment(db, actor, equipment_id)
        eid = eq.id

    return repository.list_sensors(
        db,
        equipment_id=eid,
        organization_id=org_id,
        limit=limit,
        offset=offset,
    )


def update_sensor(
    db: Session,
    *,
    actor: User,
    sensor_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Sensor:
    sensor = get_sensor(db, actor, sensor_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=sensor.organization_id):
        raise AppError("Permission denied to update this sensor.", code="FORBIDDEN", status_code=403)

    if "component_id" in changes and changes["component_id"]:
        cid = changes["component_id"] if isinstance(changes["component_id"], uuid.UUID) else uuid.UUID(str(changes["component_id"]))
        comp = eq_repo.get_component_by_id(db, cid)
        if not comp or comp.equipment_id != sensor.equipment_id:
            raise AppError("Referenced component must belong to the same equipment.", code="INVALID_COMPONENT", status_code=400)

    updated = repository.update_sensor(db, sensor_id=sensor.id, changes=changes)
    if not updated:
        raise AppError("Sensor not found.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_UPDATED,
        resource_type="sensor",
        resource_id=updated.id,
        actor_user_id=actor.id,
        organization_id=sensor.organization_id,
        metadata={"changes": list(changes.keys())},
    )
    db.commit()
    db.refresh(updated)
    return updated
