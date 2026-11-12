from collections.abc import Sequence
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models.enums import MaintenanceOutcome, VerificationStatus
from app.models.maintenance import MaintenanceRecord


def create_record(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    created_by: uuid.UUID,
    title: str,
    description: str | None = None,
    maintenance_type: str = "corrective",
    priority: str = "medium",
    status: str = "scheduled",
    diagnosis_id: uuid.UUID | None = None,
    related_alert_id: uuid.UUID | None = None,
    assigned_to: uuid.UUID | None = None,
    scheduled_at: datetime | None = None,
    inspection_timestamp: datetime | None = None,
    symptoms: str | None = None,
    diagnostic_findings: str | None = None,
    work_performed: str | None = None,
    parts_replaced_json: list[Any] | None = None,
    notes: str | None = None,
) -> MaintenanceRecord:
    record = MaintenanceRecord(
        organization_id=organization_id,
        equipment_id=equipment_id,
        created_by=created_by,
        title=title,
        description=description,
        maintenance_type=maintenance_type,
        priority=priority,
        status=status,
        diagnosis_id=diagnosis_id,
        related_alert_id=related_alert_id,
        assigned_to=assigned_to,
        scheduled_at=scheduled_at,
        inspection_timestamp=inspection_timestamp,
        symptoms=symptoms,
        diagnostic_findings=diagnostic_findings,
        work_performed=work_performed,
        parts_replaced_json=parts_replaced_json,
        notes=notes,
        outcome=MaintenanceOutcome.PENDING_VERIFICATION.value,
        verification_status=VerificationStatus.PENDING.value,
    )
    db.add(record)
    db.flush()
    return record


def get_record(db: Session, record_id: uuid.UUID | str) -> MaintenanceRecord | None:
    rid = record_id if isinstance(record_id, uuid.UUID) else uuid.UUID(str(record_id))
    return db.scalar(
        select(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.equipment),
            joinedload(MaintenanceRecord.diagnosis),
            joinedload(MaintenanceRecord.related_alert),
            joinedload(MaintenanceRecord.creator),
            joinedload(MaintenanceRecord.assignee),
            joinedload(MaintenanceRecord.verifier),
            joinedload(MaintenanceRecord.attachments),
        )
        .where(MaintenanceRecord.id == rid)
    )


def list_records(
    db: Session,
    *,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    priority: str | None = None,
    outcome: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[MaintenanceRecord]:
    stmt = (
        select(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.equipment),
            joinedload(MaintenanceRecord.attachments),
        )
        .order_by(MaintenanceRecord.created_at.desc(), MaintenanceRecord.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if organization_id is not None:
        oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(MaintenanceRecord.organization_id == oid)
    if equipment_id is not None:
        eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
        stmt = stmt.where(MaintenanceRecord.equipment_id == eid)
    if status is not None:
        stmt = stmt.where(MaintenanceRecord.status == status)
    if priority is not None:
        stmt = stmt.where(MaintenanceRecord.priority == priority)
    if outcome is not None:
        stmt = stmt.where(MaintenanceRecord.outcome == outcome)

    return db.scalars(stmt).unique().all()


def update_record(
    db: Session,
    record: MaintenanceRecord,
    **kwargs: Any,
) -> MaintenanceRecord:
    for key, value in kwargs.items():
        if value is not None and hasattr(record, key):
            setattr(record, key, value)
    record.updated_at = utcnow()
    db.flush()
    return record


def verify_record(
    db: Session,
    record: MaintenanceRecord,
    *,
    verifier_id: uuid.UUID,
    verification_status: str,
    verification_note: str | None = None,
) -> MaintenanceRecord:
    record.verification_status = verification_status
    record.verified_by = verifier_id
    record.verified_at = utcnow()
    record.verification_note = verification_note
    record.updated_at = utcnow()
    if verification_status == VerificationStatus.VERIFIED.value and record.outcome == MaintenanceOutcome.PENDING_VERIFICATION.value:
        record.outcome = MaintenanceOutcome.RESOLVED.value
    db.flush()
    return record
