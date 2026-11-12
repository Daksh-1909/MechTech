from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import Alert, Diagnosis, MaintenanceRecord, User
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import service as eq_service
from app.modules.files.schemas import StoredFileResponse
from app.modules.maintenance import repository
from app.modules.maintenance.schemas import (
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdate,
    MaintenanceVerifyRequest,
)


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def _build_response(record: MaintenanceRecord) -> MaintenanceRecordResponse:
    eq_name = record.equipment.name if record.equipment else None
    eq_tag = record.equipment.asset_tag if record.equipment else None

    attachments = [
        StoredFileResponse.model_validate(f)
        for f in getattr(record, "attachments", [])
    ]

    return MaintenanceRecordResponse(
        id=record.id,
        organization_id=record.organization_id,
        equipment_id=record.equipment_id,
        diagnosis_id=record.diagnosis_id,
        related_alert_id=record.related_alert_id,
        created_by=record.created_by,
        assigned_to=record.assigned_to,
        title=record.title,
        description=record.description,
        maintenance_type=record.maintenance_type,
        status=record.status,
        priority=record.priority,
        scheduled_at=record.scheduled_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        inspection_timestamp=record.inspection_timestamp,
        symptoms=record.symptoms,
        diagnostic_findings=record.diagnostic_findings,
        work_performed=record.work_performed,
        parts_replaced_json=record.parts_replaced_json,
        outcome=record.outcome,
        verification_status=record.verification_status,
        verified_by=record.verified_by,
        verified_at=record.verified_at,
        verification_note=record.verification_note,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
        equipment_name=eq_name,
        equipment_asset_tag=eq_tag,
        attachments=attachments,
    )


def create_record(
    db: Session,
    *,
    actor: User,
    payload: MaintenanceRecordCreate,
) -> MaintenanceRecordResponse:
    equipment = eq_service.get_equipment(db, actor, payload.equipment_id)

    if not _is_platform_admin(actor) and not has_permission(
        actor, Permission.MAINTENANCE_CREATE, organization_id=equipment.organization_id
    ):
        raise AppError("Permission denied to create maintenance records.", code="FORBIDDEN", status_code=403)

    # Validate linked diagnosis if provided
    if payload.diagnosis_id:
        diag = db.get(Diagnosis, payload.diagnosis_id)
        if not diag or diag.equipment_id != equipment.id or diag.organization_id != equipment.organization_id:
            raise AppError("Referenced diagnosis is invalid or belongs to another equipment/organization.", code="INVALID_DIAGNOSIS_REFERENCE", status_code=400)

    # Validate linked alert if provided
    if payload.related_alert_id:
        alert = db.get(Alert, payload.related_alert_id)
        if not alert or alert.equipment_id != equipment.id or alert.organization_id != equipment.organization_id:
            raise AppError("Referenced alert is invalid or belongs to another equipment/organization.", code="INVALID_ALERT_REFERENCE", status_code=400)

    record = repository.create_record(
        db,
        organization_id=equipment.organization_id,
        equipment_id=equipment.id,
        created_by=actor.id,
        title=payload.title,
        description=payload.description,
        maintenance_type=payload.maintenance_type,
        priority=payload.priority,
        status=payload.status,
        diagnosis_id=payload.diagnosis_id,
        related_alert_id=payload.related_alert_id,
        assigned_to=payload.assigned_to,
        scheduled_at=payload.scheduled_at,
        inspection_timestamp=payload.inspection_timestamp,
        symptoms=payload.symptoms,
        diagnostic_findings=payload.diagnostic_findings,
        work_performed=payload.work_performed,
        parts_replaced_json=payload.parts_replaced_json,
        notes=payload.notes,
    )

    audit_service.record_event(
        db,
        action=AuditAction.MAINTENANCE_CREATED,
        resource_type="maintenance_record",
        resource_id=record.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"title": record.title, "equipment_id": str(equipment.id), "type": record.maintenance_type},
    )

    db.commit()
    db.refresh(record)
    return _build_response(record)


def get_record(
    db: Session,
    *,
    actor: User,
    record_id: uuid.UUID | str,
) -> MaintenanceRecordResponse:
    record = repository.get_record(db, record_id)
    if not record:
        raise AppError("Maintenance record not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == record.organization_id for m in memberships):
            raise AppError("Access denied to this maintenance record.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.MAINTENANCE_VIEW, organization_id=record.organization_id):
            raise AppError("Permission denied to view maintenance records.", code="FORBIDDEN", status_code=403)

    return _build_response(record)


def list_records(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    priority: str | None = None,
    outcome: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MaintenanceRecordResponse]:
    target_org_id = None
    if organization_id:
        target_org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            target_org_id = memberships[0].organization_id

    eid = None
    if equipment_id:
        eq = eq_service.get_equipment(db, actor, equipment_id)
        eid = eq.id

    records = repository.list_records(
        db,
        organization_id=target_org_id,
        equipment_id=eid,
        status=status,
        priority=priority,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )
    return [_build_response(r) for r in records]


def update_record(
    db: Session,
    *,
    actor: User,
    record_id: uuid.UUID | str,
    payload: MaintenanceRecordUpdate,
) -> MaintenanceRecordResponse:
    record = repository.get_record(db, record_id)
    if not record:
        raise AppError("Maintenance record not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == record.organization_id for m in memberships):
            raise AppError("Access denied to this maintenance record.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.MAINTENANCE_UPDATE, organization_id=record.organization_id):
            raise AppError("Permission denied to update maintenance records.", code="FORBIDDEN", status_code=403)

    updates = payload.model_dump(exclude_unset=True)
    updated = repository.update_record(db, record, **updates)

    audit_service.record_event(
        db,
        action=AuditAction.MAINTENANCE_UPDATED,
        resource_type="maintenance_record",
        resource_id=record.id,
        actor_user_id=actor.id,
        organization_id=record.organization_id,
        metadata={"updated_fields": list(updates.keys())},
    )

    db.commit()
    db.refresh(updated)
    return _build_response(updated)


def verify_record(
    db: Session,
    *,
    actor: User,
    record_id: uuid.UUID | str,
    payload: MaintenanceVerifyRequest,
) -> MaintenanceRecordResponse:
    record = repository.get_record(db, record_id)
    if not record:
        raise AppError("Maintenance record not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == record.organization_id for m in memberships):
            raise AppError("Access denied to this maintenance record.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.MAINTENANCE_VERIFY, organization_id=record.organization_id):
            raise AppError("Permission denied to verify maintenance records.", code="FORBIDDEN", status_code=403)

    verified = repository.verify_record(
        db,
        record,
        verifier_id=actor.id,
        verification_status=payload.verification_status,
        verification_note=payload.verification_note,
    )

    audit_service.record_event(
        db,
        action=AuditAction.MAINTENANCE_VERIFIED,
        resource_type="maintenance_record",
        resource_id=record.id,
        actor_user_id=actor.id,
        organization_id=record.organization_id,
        metadata={"decision": payload.verification_status, "note": payload.verification_note},
    )

    db.commit()
    db.refresh(verified)
    return _build_response(verified)
