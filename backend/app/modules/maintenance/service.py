from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Alert, MaintenanceRecord, User, UserRole
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository as equipment_repository
from app.modules.maintenance import repository


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_record(db: Session, record_id: int) -> MaintenanceRecord:
    record = repository.get_record(db, record_id)
    if record is None:
        raise AppError("Maintenance record not found.", code="NOT_FOUND", status_code=404)
    return record


def list_records(
    db: Session,
    *,
    equipment_id: str | None,
    outcome: str | None,
    limit: int,
    offset: int,
) -> list[MaintenanceRecord]:
    return repository.list_records(
        db,
        equipment_id=equipment_id,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )


def _validate_related_alert(db: Session, *, equipment_id: str, alert_id: int | None) -> None:
    if alert_id is None:
        return
    alert = db.get(Alert, alert_id)
    if alert is None or alert.equipment_id != equipment_id:
        raise AppError(
            "The related alert does not belong to this equipment.",
            code="INVALID_ALERT_REFERENCE",
            status_code=400,
        )


def create_record(
    db: Session,
    *,
    actor: User,
    values: dict,
) -> MaintenanceRecord:
    equipment = equipment_repository.get_equipment(db, values["equipment_id"])
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    if equipment.is_archived:
        raise AppError(
            "Maintenance records cannot be created for archived equipment.",
            code="EQUIPMENT_ARCHIVED",
            status_code=409,
        )

    _validate_related_alert(
        db,
        equipment_id=values["equipment_id"],
        alert_id=values.get("related_alert_id"),
    )

    values["inspection_timestamp"] = _to_utc(values["inspection_timestamp"])
    values["outcome"] = values["outcome"].value
    values["verification_status"] = values["verification_status"].value
    record = MaintenanceRecord(technician_id=actor.id, **values)
    db.add(record)
    db.flush()
    audit_service.record_event(
        db,
        action=AuditAction.MAINTENANCE_CREATED,
        resource_type="maintenance_record",
        resource_id=record.id,
        actor_user_id=actor.id,
        metadata={"equipment_id": record.equipment_id, "outcome": record.outcome},
    )
    db.commit()
    db.refresh(record)
    return record


def update_record(
    db: Session,
    *,
    actor: User,
    record_id: int,
    changes: dict,
) -> MaintenanceRecord:
    record = get_record(db, record_id)

    is_admin = actor.role == UserRole.ADMIN.value
    if not is_admin and record.technician_id != actor.id:
        raise AppError(
            "You do not have permission to update this maintenance record.",
            code="FORBIDDEN",
            status_code=403,
        )

    updated_fields: list[str] = []
    for field, value in changes.items():
        if field in {"outcome", "verification_status"} and value is not None:
            value = value.value
        setattr(record, field, value)
        updated_fields.append(field)

    if updated_fields:
        audit_service.record_event(
            db,
            action=AuditAction.MAINTENANCE_UPDATED,
            resource_type="maintenance_record",
            resource_id=record.id,
            actor_user_id=actor.id,
            metadata={"equipment_id": record.equipment_id, "fields": updated_fields},
        )
        db.commit()
        db.refresh(record)
    return record
