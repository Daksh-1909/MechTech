from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User, UserRole


class Permission(StrEnum):
    MONITORING_VIEW = "monitoring:view"
    EQUIPMENT_VIEW = "equipment:view"
    EQUIPMENT_MANAGE = "equipment:manage"
    USERS_MANAGE = "users:manage"
    READINGS_VIEW = "readings:view"
    READINGS_INGEST = "readings:ingest"
    ALERTS_VIEW = "alerts:view"
    ALERTS_MANAGE = "alerts:manage"
    MAINTENANCE_VIEW = "maintenance:view"
    MAINTENANCE_MANAGE = "maintenance:manage"
    KNOWLEDGE_MANAGE = "knowledge:manage"
    ML_ANALYSIS_REQUEST = "ml:analysis_request"
    MODELS_VIEW = "models:view"
    AUDIT_VIEW = "audit:view"


_ALL_PERMISSIONS = frozenset(Permission)

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "admin": _ALL_PERMISSIONS,
    "technician": frozenset(
        {
            Permission.MONITORING_VIEW,
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.READINGS_INGEST,
            Permission.ALERTS_VIEW,
            Permission.ALERTS_MANAGE,
            Permission.MAINTENANCE_VIEW,
            Permission.MAINTENANCE_MANAGE,
            Permission.ML_ANALYSIS_REQUEST,
            Permission.MODELS_VIEW,
        }
    ),
    "operator": frozenset(
        {
            Permission.MONITORING_VIEW,
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.ALERTS_VIEW,
            Permission.MAINTENANCE_VIEW,
        }
    ),
}


def normalize_role(role: str | UserRole) -> str:
    return getattr(role, "value", role)


def role_has_permission(role: str | UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(normalize_role(role), frozenset())


def has_permission(user: User, permission: Permission) -> bool:
    return user.is_active and role_has_permission(user.role, permission)


def ensure_permission(user: User, permission: Permission) -> None:
    from app.core.exceptions import AppError

    if not has_permission(user, permission):
        raise AppError(
            "You do not have permission to perform this action.",
            code="FORBIDDEN",
            status_code=403,
        )
