from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def create_audit_log(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    actor_user_id: uuid.UUID | str | None,
    organization_id: uuid.UUID | str | None = None,
    timestamp: datetime,
    request_id: str | None,
    metadata_json: dict[str, Any] | None,
) -> AuditLog:
    parsed_actor = None
    if actor_user_id:
        parsed_actor = actor_user_id if isinstance(actor_user_id, uuid.UUID) else uuid.UUID(str(actor_user_id))

    parsed_org = None
    if organization_id:
        parsed_org = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))

    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_user_id=parsed_actor,
        organization_id=parsed_org,
        timestamp=timestamp,
        request_id=request_id,
        details=metadata_json,
    )
    db.add(entry)
    db.flush()
    return entry


def list_audit_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
    organization_id: uuid.UUID | str | None = None,
) -> list[AuditLog]:
    stmt = select(AuditLog)
    if organization_id is not None:
        parsed_org = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(AuditLog.organization_id == parsed_org)
    stmt = stmt.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))
