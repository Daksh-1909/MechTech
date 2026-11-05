from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def create_audit_log(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    actor_user_id: int | None,
    timestamp: datetime,
    request_id: str | None,
    metadata_json: dict[str, Any] | None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_user_id=actor_user_id,
        timestamp=timestamp,
        request_id=request_id,
        metadata_json=metadata_json,
    )
    db.add(entry)
    db.flush()
    return entry


def list_audit_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
