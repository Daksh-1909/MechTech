from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.user import User


class Permission(StrEnum):
    # User and access management
    USER_CREATE = "user.create"
    USER_APPROVE = "user.approve"
    USER_SUSPEND = "user.suspend"
    USER_VIEW = "user.view"

    # Organization management
    ORGANIZATION_CREATE = "organization.create"
    ORGANIZATION_MANAGE = "organization.manage"
    ORGANIZATION_VIEW = "organization.view"

    # Equipment
    EQUIPMENT_CREATE = "equipment.create"
    EQUIPMENT_UPDATE = "equipment.update"
    EQUIPMENT_ARCHIVE = "equipment.archive"
    EQUIPMENT_VIEW = "equipment.view"

    # Telemetry and sensors
    SENSOR_MANAGE = "sensor.manage"
    READINGS_VIEW = "sensor.readings.view"
    READINGS_INGEST = "sensor.readings.ingest"

    # Monitoring and alerts
    MONITORING_RULES_MANAGE = "monitoring.rules.manage"
    MONITORING_RULES_VIEW = "monitoring.rules.view"
    ALERT_ACKNOWLEDGE = "alert.acknowledge"
    ALERT_RESOLVE = "alert.resolve"
    ALERT_DISMISS = "alert.dismiss"
    ALERT_VIEW = "alert.view"

    # Diagnostics and ML
    DIAGNOSIS_GENERATE = "diagnosis.generate"
    DIAGNOSIS_REVIEW = "diagnosis.review"
    DIAGNOSIS_VIEW = "diagnosis.view"
    ML_MODEL_MANAGE = "ml.model.manage"
    ML_MODEL_VIEW = "ml.model.view"

    # Knowledge graph
    KNOWLEDGE_MANAGE = "knowledge.manage"
    KNOWLEDGE_VIEW = "knowledge.view"

    # Maintenance
    MAINTENANCE_CREATE = "maintenance.create"
    MAINTENANCE_UPDATE = "maintenance.update"
    MAINTENANCE_VERIFY = "maintenance.verify"
    MAINTENANCE_VIEW = "maintenance.view"

    # Files and audit
    FILES_UPLOAD = "files.upload"
    FILES_DOWNLOAD = "files.download"
    AUDIT_VIEW = "audit.view"

    # Legacy enum aliases for existing code compatibility
    MONITORING_VIEW = "monitoring.rules.view"
    EQUIPMENT_MANAGE = "equipment.create"
    USERS_MANAGE = "user.create"
    ALERTS_VIEW = "alert.view"
    ALERTS_MANAGE = "alert.acknowledge"
    ML_ANALYSIS_REQUEST = "diagnosis.generate"
    MODELS_VIEW = "ml.model.view"
    MODEL_MANAGE = "ml.model.manage"


_ALL_PERMISSIONS = frozenset(
    p for p in Permission if "." in p.value
)

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "platform_admin": _ALL_PERMISSIONS,
    "org_admin": frozenset(
        {
            Permission.USER_CREATE,
            Permission.USER_APPROVE,
            Permission.USER_SUSPEND,
            Permission.USER_VIEW,
            Permission.ORGANIZATION_MANAGE,
            Permission.ORGANIZATION_VIEW,
            Permission.EQUIPMENT_CREATE,
            Permission.EQUIPMENT_UPDATE,
            Permission.EQUIPMENT_ARCHIVE,
            Permission.EQUIPMENT_VIEW,
            Permission.SENSOR_MANAGE,
            Permission.READINGS_VIEW,
            Permission.READINGS_INGEST,
            Permission.MONITORING_RULES_MANAGE,
            Permission.MONITORING_RULES_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
            Permission.ALERT_RESOLVE,
            Permission.ALERT_DISMISS,
            Permission.ALERT_VIEW,
            Permission.DIAGNOSIS_GENERATE,
            Permission.DIAGNOSIS_REVIEW,
            Permission.DIAGNOSIS_VIEW,
            Permission.ML_MODEL_MANAGE,
            Permission.ML_MODEL_VIEW,
            Permission.KNOWLEDGE_MANAGE,
            Permission.KNOWLEDGE_VIEW,
            Permission.MAINTENANCE_CREATE,
            Permission.MAINTENANCE_UPDATE,
            Permission.MAINTENANCE_VERIFY,
            Permission.MAINTENANCE_VIEW,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.AUDIT_VIEW,
        }
    ),
    "maintainer": frozenset(
        {
            Permission.EQUIPMENT_VIEW,
            Permission.EQUIPMENT_UPDATE,
            Permission.READINGS_VIEW,
            Permission.READINGS_INGEST,
            Permission.MONITORING_RULES_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
            Permission.ALERT_RESOLVE,
            Permission.ALERT_DISMISS,
            Permission.ALERT_VIEW,
            Permission.DIAGNOSIS_GENERATE,
            Permission.DIAGNOSIS_REVIEW,
            Permission.DIAGNOSIS_VIEW,
            Permission.ML_MODEL_VIEW,
            Permission.KNOWLEDGE_VIEW,
            Permission.MAINTENANCE_CREATE,
            Permission.MAINTENANCE_UPDATE,
            Permission.MAINTENANCE_VERIFY,
            Permission.MAINTENANCE_VIEW,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
        }
    ),
    "viewer": frozenset(
        {
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.MONITORING_RULES_VIEW,
            Permission.ALERT_VIEW,
            Permission.DIAGNOSIS_VIEW,
            Permission.ML_MODEL_VIEW,
            Permission.KNOWLEDGE_VIEW,
            Permission.MAINTENANCE_VIEW,
            Permission.FILES_DOWNLOAD,
        }
    ),
    "demo_user": frozenset(
        {
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.MONITORING_RULES_VIEW,
            Permission.ALERT_VIEW,
            Permission.DIAGNOSIS_VIEW,
            Permission.ML_MODEL_VIEW,
            Permission.KNOWLEDGE_VIEW,
            Permission.MAINTENANCE_VIEW,
        }
    ),
    # Legacy aliases
    "admin": _ALL_PERMISSIONS,
    "technician": frozenset(
        {
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.READINGS_INGEST,
            Permission.ALERT_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
            Permission.MAINTENANCE_VIEW,
            Permission.MAINTENANCE_CREATE,
            Permission.DIAGNOSIS_GENERATE,
            Permission.ML_MODEL_VIEW,
        }
    ),
    "operator": frozenset(
        {
            Permission.EQUIPMENT_VIEW,
            Permission.READINGS_VIEW,
            Permission.ALERT_VIEW,
            Permission.MAINTENANCE_VIEW,
        }
    ),
}


def get_user_permissions(user: User, organization_id: uuid.UUID | str | None = None) -> set[Permission]:
    """Retrieve all effective permissions for a user across roles or for a specific organization."""
    if not user.is_active:
        return set()

    permissions: set[Permission] = set()

    org_uuid: uuid.UUID | None = None
    if organization_id is not None:
        org_uuid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))

    # Check assigned roles
    for assignment in getattr(user, "assigned_roles", []):
        role_key = assignment.role.key if assignment.role else None
        if not role_key:
            continue

        # If platform role, always applies
        is_platform = assignment.role.scope == "platform"
        # If organization role, applies if organization matches or if unconstrained check
        is_org_match = (
            assignment.role.scope == "organization"
            and (org_uuid is None or assignment.organization_id == org_uuid)
        )

        if is_platform or is_org_match:
            # Add permissions from DB role if populated
            if assignment.role.role_permissions:
                for rp in assignment.role.role_permissions:
                    try:
                        permissions.add(Permission(rp.permission.key))
                    except ValueError:
                        pass
            # Also add from predefined ROLE_PERMISSIONS mapping
            if role_key in ROLE_PERMISSIONS:
                permissions.update(ROLE_PERMISSIONS[role_key])

    return permissions


def has_permission(
    user: User,
    permission: Permission,
    organization_id: uuid.UUID | str | None = None,
) -> bool:
    """Check if user has a specific permission."""
    if not user.is_active:
        return False
    user_perms = get_user_permissions(user, organization_id)
    return permission in user_perms


def ensure_permission(
    user: User,
    permission: Permission,
    organization_id: uuid.UUID | str | None = None,
) -> None:
    from app.core.exceptions import AppError

    if not has_permission(user, permission, organization_id):
        raise AppError(
            "You do not have permission to perform this action.",
            code="FORBIDDEN",
            status_code=403,
        )
