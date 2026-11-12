from enum import StrEnum


class EquipmentStatus(StrEnum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    ARCHIVED = "archived"


class ReadingQuality(StrEnum):
    VALID = "valid"
    PARTIAL = "partial"


class RuleOperator(StrEnum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class MaintenanceOutcome(StrEnum):
    RESOLVED = "resolved"
    NOT_RESOLVED = "not_resolved"
    INCONCLUSIVE = "inconclusive"
    PENDING_VERIFICATION = "pending_verification"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class MaintenanceType(StrEnum):
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    CONDITION_BASED = "condition_based"
    EMERGENCY = "emergency"


class MaintenanceStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenancePriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FilePurpose(StrEnum):
    MAINTENANCE_ATTACHMENT = "maintenance_attachment"
    VIBRATION_REPORT = "vibration_report"
    INSPECTION_PHOTO = "inspection_photo"
    MANUAL = "manual"
    GENERAL = "general"


class ModelType(StrEnum):
    ANOMALY = "anomaly"
    CLASSIFICATION = "classification"


class ModelStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    RETIRED = "retired"


class DiagnosisStatus(StrEnum):
    NORMAL = "normal"
    ATTENTION_REQUIRED = "attention_required"
    POSSIBLE_FAULT = "possible_fault"
    INSUFFICIENT_DATA = "insufficient_data"
    UNDER_REVIEW = "under_review"
    CONFIRMED_BY_REVIEWER = "confirmed_by_reviewer"
    DISMISSED = "dismissed"


class EvidenceType(StrEnum):
    RULE = "rule"
    PREDICTION = "prediction"
    GRAPH = "graph"
    SENSOR = "sensor"
    MANUAL = "manual"


class TrainingJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NodeType(StrEnum):
    EQUIPMENT = "equipment"
    COMPONENT = "component"
    SENSOR = "sensor"
    SYMPTOM = "symptom"
    FAULT = "fault"
    DIAGNOSTIC_STEP = "diagnostic_step"
    REPAIR_ACTION = "repair_action"
    PART = "part"
    MAINTENANCE_RECORD = "maintenance_record"


class RelationshipType(StrEnum):
    HAS_COMPONENT = "HAS_COMPONENT"
    HAS_SENSOR = "HAS_SENSOR"
    MONITORS = "MONITORS"
    MAY_CAUSE = "MAY_CAUSE"
    INDICATES = "INDICATES"
    AFFECTS = "AFFECTS"
    CHECK_WITH = "CHECK_WITH"
    MAY_BE_RESOLVED_BY = "MAY_BE_RESOLVED_BY"
    REQUIRES_PART = "REQUIRES_PART"
    RECORDED_IN = "RECORDED_IN"


INTEGRITY_CHECKS: dict[str, str] = {
    "ck_equipment_status": "status IN ('active', 'maintenance', 'out_of_service', 'archived')",
    "ck_readings_quality": "quality_status IN ('valid', 'partial')",
    "ck_readings_at_least_one_channel": (
        "temperature_c IS NOT NULL OR vibration_value IS NOT NULL"
    ),
    "ck_monitoring_rules_operator": "operator IN ('gt', 'gte', 'lt', 'lte', 'eq', 'neq')",
    "ck_monitoring_rules_severity": "severity IN ('low', 'medium', 'high', 'critical')",
    "ck_anomaly_severity": "severity IN ('low', 'medium', 'high', 'critical')",
    "ck_anomaly_review": "review_status IN ('pending', 'confirmed', 'rejected')",
    "ck_alerts_severity": "severity IN ('low', 'medium', 'high', 'critical')",
    "ck_alerts_status": "status IN ('open', 'acknowledged', 'resolved', 'dismissed')",
    "ck_diagnoses_status": (
        "status IN ('normal', 'attention_required', 'possible_fault', 'insufficient_data', "
        "'under_review', 'confirmed_by_reviewer', 'dismissed')"
    ),
    "ck_diagnosis_evidence_type": (
        "evidence_type IN ('rule', 'prediction', 'graph', 'sensor', 'manual')"
    ),
    "ck_ml_models_status": "status IN ('draft', 'validated', 'active', 'retired')",
    "ck_predictions_review": "review_status IN ('pending', 'confirmed', 'rejected')",
    "ck_models_type": "model_type IN ('anomaly', 'classification')",
    "ck_maintenance_outcome": (
        "outcome IN ('resolved', 'not_resolved', 'inconclusive', 'pending_verification')"
    ),
    "ck_maintenance_verification": ("verification_status IN ('pending', 'verified', 'rejected')"),
    "ck_maintenance_type": (
        "maintenance_type IN ('corrective', 'preventive', 'condition_based', 'emergency')"
    ),
    "ck_maintenance_status": (
        "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')"
    ),
    "ck_maintenance_priority": (
        "priority IN ('low', 'medium', 'high', 'critical')"
    ),
    "ck_stored_files_purpose": (
        "purpose IN ('maintenance_attachment', 'vibration_report', 'inspection_photo', 'manual', 'general')"
    ),
    "ck_knowledge_node_type": (
        "node_type IN ('equipment', 'component', 'sensor', 'symptom', 'fault', "
        "'diagnostic_step', 'repair_action', 'part', 'maintenance_record')"
    ),
    "ck_knowledge_edge_type": (
        "relationship_type IN ('HAS_COMPONENT', 'HAS_SENSOR', 'MONITORS', 'MAY_CAUSE', "
        "'INDICATES', 'AFFECTS', 'CHECK_WITH', 'MAY_BE_RESOLVED_BY', 'REQUIRES_PART', "
        "'RECORDED_IN')"
    ),
}
