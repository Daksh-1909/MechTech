import json
import re
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_request_id
from app.core.time import utcnow
from app.models import AuditLog
from app.modules.audit import repository

_MAX_METADATA_BYTES = 4096
_MAX_STRING_LENGTH = 200
_MAX_COLLECTION_ITEMS = 20
_MAX_DEPTH = 4

_SENSITIVE_KEY = re.compile(
    r"(password|passwd|token|cookie|secret|authorization|api[_-]?key|csrf)",
    re.IGNORECASE,
)
_REDACTED = "[redacted]"


def _sanitize(value: Any, depth: int = 0) -> Any:
    if depth > _MAX_DEPTH:
        return _REDACTED

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= _MAX_COLLECTION_ITEMS:
                sanitized["_truncated"] = True
                break
            key_text = str(key)[:_MAX_STRING_LENGTH]
            sanitized[key_text] = (
                _REDACTED if _SENSITIVE_KEY.search(key_text) else _sanitize(item, depth + 1)
            )
        return sanitized

    if isinstance(value, (list, tuple)):
        return [_sanitize(item, depth + 1) for item in value[:_MAX_COLLECTION_ITEMS]]

    if isinstance(value, str):
        return value[:_MAX_STRING_LENGTH]

    if isinstance(value, (bool, int, float)) or value is None:
        return value

    return str(value)[:_MAX_STRING_LENGTH]


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None

    sanitized = _sanitize(metadata)
    encoded = json.dumps(sanitized, ensure_ascii=True, default=str)
    if len(encoded.encode("utf-8")) > _MAX_METADATA_BYTES:
        return {"truncated": True, "reason": "metadata_too_large"}
    return sanitized


def record_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | int | uuid.UUID | None = None,
    actor_user_id: uuid.UUID | str | int | None = None,
    organization_id: uuid.UUID | str | None = None,
    metadata: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> None:
    repository.create_audit_log(
        db,
        action=action,
        resource_type=resource_type,
        resource_id=None if resource_id is None else str(resource_id),
        actor_user_id=None if actor_user_id is None else str(actor_user_id),
        organization_id=organization_id,
        timestamp=utcnow(),
        request_id=request_id or get_request_id(),
        metadata_json=sanitize_metadata(metadata),
    )


def list_events(
    db: Session,
    *,
    limit: int,
    offset: int,
    organization_id: uuid.UUID | str | None = None,
) -> list[AuditLog]:
    return repository.list_audit_logs(db, limit=limit, offset=offset, organization_id=organization_id)
