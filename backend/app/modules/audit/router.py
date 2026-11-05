from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.audit import service
from app.modules.audit.actions import AuditAction
from app.modules.audit.schemas import AuditLogResponse
from app.modules.auth.dependencies import require_permission

router = APIRouter()

AuditViewer = Annotated[User, Depends(require_permission(Permission.AUDIT_VIEW))]


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: DbSession,
    viewer: AuditViewer,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogResponse]:
    service.record_event(
        db,
        action=AuditAction.AUDIT_LOGS_VIEWED,
        resource_type="audit_log",
        actor_user_id=viewer.id,
        metadata={"limit": limit, "offset": offset},
    )
    db.commit()

    entries = service.list_events(db, limit=limit, offset=offset)
    return [AuditLogResponse.model_validate(entry) for entry in entries]
