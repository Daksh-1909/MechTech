from enum import StrEnum


class AuditAction(StrEnum):
    # Authentication
    AUTH_LOGIN_SUCCEEDED = "auth.login_succeeded"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"  # noqa: S105

    # Registration workflow
    REGISTRATION_SUBMITTED = "registration.submitted"
    REGISTRATION_APPROVED = "registration.approved"
    REGISTRATION_REJECTED = "registration.rejected"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_ROLE_ASSIGNED = "user.role_assigned"
    USER_STATUS_CHANGED = "user.status_changed"
    USER_SUSPENDED = "user.suspended"
    USER_ACTIVATED = "user.activated"

    # Organizations
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_MEMBER_ADDED = "organization.member_added"
    ORGANIZATION_MEMBER_REMOVED = "organization.member_removed"

    # Equipment
    EQUIPMENT_CREATED = "equipment.created"
    EQUIPMENT_UPDATED = "equipment.updated"
    EQUIPMENT_ARCHIVED = "equipment.archived"
    COMPONENT_CREATED = "component.created"
    COMPONENT_UPDATED = "component.updated"

    # Alerts & Monitoring
    MONITORING_RULE_CREATED = "monitoring_rule.created"
    MONITORING_RULE_UPDATED = "monitoring_rule.updated"
    MONITORING_RULE_DELETED = "monitoring_rule.deleted"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_DISMISSED = "alert.dismissed"

    # Diagnostics & ML
    DIAGNOSIS_GENERATED = "diagnosis.generated"
    DIAGNOSIS_REVIEWED = "diagnosis.reviewed"
    MODEL_REGISTERED = "model.registered"
    MODEL_ACTIVATED = "model.activated"

    # Maintenance
    MAINTENANCE_CREATED = "maintenance.created"
    MAINTENANCE_UPDATED = "maintenance.updated"
    MAINTENANCE_VERIFIED = "maintenance.verified"

    # Files
    FILE_UPLOADED = "file.uploaded"
    FILE_DOWNLOADED = "file.downloaded"

    # Knowledge
    KNOWLEDGE_NODE_CREATED = "knowledge.node_created"
    KNOWLEDGE_NODE_UPDATED = "knowledge.node_updated"
    KNOWLEDGE_EDGE_CREATED = "knowledge.edge_created"

    # Auditing
    AUDIT_LOGS_VIEWED = "audit.logs_viewed"
