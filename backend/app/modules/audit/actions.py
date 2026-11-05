from enum import StrEnum


class AuditAction(StrEnum):
    AUTH_LOGIN_SUCCEEDED = "auth.login_succeeded"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"  # noqa: S105

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_STATUS_CHANGED = "user.status_changed"

    EQUIPMENT_CREATED = "equipment.created"
    EQUIPMENT_UPDATED = "equipment.updated"
    EQUIPMENT_ARCHIVED = "equipment.archived"
    COMPONENT_CREATED = "component.created"
    COMPONENT_UPDATED = "component.updated"

    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_DISMISSED = "alert.dismissed"

    MAINTENANCE_CREATED = "maintenance.created"
    MAINTENANCE_UPDATED = "maintenance.updated"

    MODEL_REGISTERED = "model.registered"
    MODEL_ACTIVATED = "model.activated"
    KNOWLEDGE_NODE_CREATED = "knowledge.node_created"
    KNOWLEDGE_NODE_UPDATED = "knowledge.node_updated"
    KNOWLEDGE_EDGE_CREATED = "knowledge.edge_created"

    AUDIT_LOGS_VIEWED = "audit.logs_viewed"
