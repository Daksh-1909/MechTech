"""Monitoring service: rule management, threshold evaluation engine, and equipment status."""

from datetime import datetime, timedelta
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.core.time import utcnow
from app.models import Alert, AnomalyEvent, Equipment, SensorReading, User
from app.models.enums import AlertStatus, RuleOperator, Severity
from app.models.monitoring_rule import MonitoringRule
from app.modules.alerts import repository as alert_repo
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository as eq_repo
from app.modules.equipment import service as eq_service
from app.modules.monitoring import repository as rule_repo
from app.modules.monitoring.schemas import (
    EquipmentStatusResponse,
    MonitoringRuleCreateRequest,
    MonitoringRuleResponse,
    MonitoringRuleUpdateRequest,
    ReadingSnapshot,
)


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


# ---------------------------------------------------------------------------
# Monitoring Rules CRUD
# ---------------------------------------------------------------------------


def create_rule(
    db: Session,
    *,
    actor: User,
    payload: MonitoringRuleCreateRequest,
) -> MonitoringRuleResponse:
    org_id = payload.organization_id
    if org_id is None:
        memberships = getattr(actor, "memberships", [])
        if memberships:
            org_id = memberships[0].organization_id
        elif not _is_platform_admin(actor):
            raise AppError("Organization ID is required.", code="ORG_REQUIRED", status_code=400)

    if org_id is not None:
        org_id = eq_service.resolve_organization_for_actor(actor, org_id)

    if not _is_platform_admin(actor) and not has_permission(
        actor, Permission.MONITORING_RULES_MANAGE, organization_id=org_id
    ):
        raise AppError("Permission denied to manage monitoring rules.", code="FORBIDDEN", status_code=403)

    if payload.equipment_type_id is not None:
        eq_type = db.get(eq_repo.EquipmentType, payload.equipment_type_id)
        if not eq_type:
            raise AppError("Referenced equipment type does not exist.", code="INVALID_EQUIPMENT_TYPE", status_code=400)

    rule = rule_repo.create_rule(
        db,
        organization_id=org_id,
        equipment_type_id=payload.equipment_type_id,
        name=payload.name,
        measurement_type=payload.measurement_type,
        operator=payload.operator.value if hasattr(payload.operator, "value") else str(payload.operator),
        threshold=payload.threshold,
        unit=payload.unit,
        duration_seconds=payload.duration_seconds,
        severity=payload.severity.value if hasattr(payload.severity, "value") else str(payload.severity),
        is_enabled=payload.is_enabled,
        created_by=actor.id,
    )

    audit_service.record_event(
        db,
        action=AuditAction.MONITORING_RULE_CREATED,
        resource_type="monitoring_rule",
        resource_id=rule.id,
        actor_user_id=actor.id,
        organization_id=org_id,
        metadata={"name": rule.name, "measurement_type": rule.measurement_type, "threshold": rule.threshold},
    )
    db.commit()
    db.refresh(rule)
    return MonitoringRuleResponse.model_validate(rule)


def get_rule(
    db: Session,
    actor: User,
    rule_id: uuid.UUID | str,
) -> MonitoringRuleResponse:
    rule = rule_repo.get_rule_by_id(db, rule_id)
    if not rule:
        raise AppError("Monitoring rule not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == rule.organization_id for m in memberships):
            raise AppError("Access denied to this monitoring rule.", code="FORBIDDEN", status_code=403)

    return MonitoringRuleResponse.model_validate(rule)


def list_rules(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
    equipment_type_id: uuid.UUID | str | None = None,
    measurement_type: str | None = None,
    is_enabled: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MonitoringRuleResponse]:
    target_org_id = None
    if organization_id:
        target_org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            target_org_id = memberships[0].organization_id

    rules = rule_repo.list_rules(
        db,
        organization_id=target_org_id,
        equipment_type_id=equipment_type_id,
        measurement_type=measurement_type,
        is_enabled=is_enabled,
        limit=limit,
        offset=offset,
    )
    return [MonitoringRuleResponse.model_validate(r) for r in rules]


def update_rule(
    db: Session,
    *,
    actor: User,
    rule_id: uuid.UUID | str,
    payload: MonitoringRuleUpdateRequest,
) -> MonitoringRuleResponse:
    existing = rule_repo.get_rule_by_id(db, rule_id)
    if not existing:
        raise AppError("Monitoring rule not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor) and not has_permission(
        actor, Permission.MONITORING_RULES_MANAGE, organization_id=existing.organization_id
    ):
        raise AppError("Permission denied to update this monitoring rule.", code="FORBIDDEN", status_code=403)

    changes = payload.model_dump(exclude_unset=True)
    if "operator" in changes and changes["operator"]:
        changes["operator"] = changes["operator"].value if hasattr(changes["operator"], "value") else str(changes["operator"])
    if "severity" in changes and changes["severity"]:
        changes["severity"] = changes["severity"].value if hasattr(changes["severity"], "value") else str(changes["severity"])

    updated = rule_repo.update_rule(db, rule_id=existing.id, changes=changes)
    audit_service.record_event(
        db,
        action=AuditAction.MONITORING_RULE_UPDATED,
        resource_type="monitoring_rule",
        resource_id=existing.id,
        actor_user_id=actor.id,
        organization_id=existing.organization_id,
        metadata={"changes": list(changes.keys())},
    )
    db.commit()
    db.refresh(updated)
    return MonitoringRuleResponse.model_validate(updated)


def delete_rule(
    db: Session,
    *,
    actor: User,
    rule_id: uuid.UUID | str,
) -> None:
    existing = rule_repo.get_rule_by_id(db, rule_id)
    if not existing:
        raise AppError("Monitoring rule not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor) and not has_permission(
        actor, Permission.MONITORING_RULES_MANAGE, organization_id=existing.organization_id
    ):
        raise AppError("Permission denied to delete this monitoring rule.", code="FORBIDDEN", status_code=403)

    rule_repo.delete_rule(db, rule_id=existing.id)
    audit_service.record_event(
        db,
        action=AuditAction.MONITORING_RULE_DELETED,
        resource_type="monitoring_rule",
        resource_id=existing.id,
        actor_user_id=actor.id,
        organization_id=existing.organization_id,
        metadata={"name": existing.name},
    )
    db.commit()


# ---------------------------------------------------------------------------
# Reading Evaluation Engine (Thresholds, Durations & Alert Generation)
# ---------------------------------------------------------------------------


def _extract_metric_value(reading: SensorReading, measurement_type: str) -> float | None:
    m = measurement_type.lower()
    if m in ("temperature", "temperature_c", "temp"):
        return reading.temperature_c if reading.temperature_c is not None else reading.value
    if m in ("vibration", "vibration_value", "vib"):
        return reading.vibration_value if reading.vibration_value is not None else reading.value
    if m in ("speed", "speed_rpm", "rpm"):
        return reading.speed_rpm
    if m in ("load", "load_percent"):
        return reading.load_percent
    return reading.value


def _evaluate_operator(value: float, operator: str, threshold: float) -> bool:
    op = operator.lower()
    if op == RuleOperator.GT.value:
        return value > threshold
    if op == RuleOperator.GTE.value:
        return value >= threshold
    if op == RuleOperator.LT.value:
        return value < threshold
    if op == RuleOperator.LTE.value:
        return value <= threshold
    if op == RuleOperator.EQ.value:
        return value == threshold
    if op == RuleOperator.NEQ.value:
        return value != threshold
    return False


def _check_duration_condition(
    db: Session,
    reading: SensorReading,
    rule: MonitoringRule,
) -> bool:
    """Verify if the rule condition has been sustained over duration_seconds."""
    if rule.duration_seconds <= 0:
        return True

    window_start = reading.timestamp - timedelta(seconds=rule.duration_seconds)
    history = list(
        db.scalars(
            select(SensorReading)
            .where(
                SensorReading.equipment_id == reading.equipment_id,
                SensorReading.timestamp >= window_start,
                SensorReading.timestamp <= reading.timestamp,
            )
            .order_by(SensorReading.timestamp.asc())
        )
    )
    if not history:
        return True

    # Check whether the window spans the required duration and every reading violated
    time_span = (history[-1].timestamp - history[0].timestamp).total_seconds()
    if time_span < rule.duration_seconds * 0.8:  # Allow 20% jitter tolerance
        return False

    for item in history:
        val = _extract_metric_value(item, rule.measurement_type)
        if val is None or not _evaluate_operator(val, rule.operator, rule.threshold):
            return False

    return True


def evaluate_reading(db: Session, reading: SensorReading) -> list[AnomalyEvent]:
    """Evaluate reading against all active rules for the equipment.

    Generates AnomalyEvent records and Alert notifications when violated.
    If no custom rules exist, evaluates prototype defaults.
    """
    equipment = eq_repo.get_equipment_by_id(db, reading.equipment_id)
    if not equipment:
        return []

    rules = rule_repo.get_active_rules_for_equipment(
        db,
        organization_id=equipment.organization_id,
        equipment_type_id=equipment.equipment_type_id,
    )

    detected_events: list[AnomalyEvent] = []

    # 1. Custom Rules Evaluation
    if rules:
        violated_rules: list[MonitoringRule] = []
        for rule in rules:
            val = _extract_metric_value(reading, rule.measurement_type)
            if val is None:
                continue

            if _evaluate_operator(val, rule.operator, rule.threshold):
                if _check_duration_condition(db, reading, rule):
                    violated_rules.append(rule)

        if not violated_rules:
            # All normal -> close any active anomalies for this equipment
            alert_repo.close_open_anomalies(db, equipment_id=equipment.id, timestamp=reading.timestamp)
            db.commit()
            return []

        for rule in violated_rules:
            val = _extract_metric_value(reading, rule.measurement_type)
            evidence = {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "reading_id": str(reading.id),
                "measurement_type": rule.measurement_type,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "actual_value": val,
                "unit": rule.unit,
                "duration_seconds": rule.duration_seconds,
                "disclaimer": "Advisory alert based on simulated data and configured rules. Verification required.",
            }

            open_anomaly = alert_repo.find_open_anomaly_event(
                db,
                equipment_id=equipment.id,
                rule_id=rule.id,
            )
            if open_anomaly:
                open_anomaly.end_timestamp = reading.timestamp
                open_anomaly.evidence_json = evidence
                open_anomaly.severity = rule.severity
                anomaly_event = open_anomaly
            else:
                anomaly_event = alert_repo.create_anomaly_event(
                    db,
                    organization_id=equipment.organization_id,
                    equipment_id=equipment.id,
                    rule_id=rule.id,
                    sensor_id=reading.sensor_id,
                    event_type=f"rule_violation_{rule.measurement_type}",
                    severity=rule.severity,
                    summary=f"Rule '{rule.name}' threshold exceeded ({val} {rule.unit})",
                    start_timestamp=reading.timestamp,
                    evidence_json=evidence,
                    status="detected",
                )

            # Ensure an active Alert is linked
            open_alert = alert_repo.find_open_alert(
                db,
                equipment_id=equipment.id,
                alert_type=f"rule_{rule.id}",
            )
            if not open_alert:
                alert_repo.create_alert(
                    db,
                    organization_id=equipment.organization_id,
                    equipment_id=equipment.id,
                    anomaly_event_id=anomaly_event.id,
                    alert_type=f"rule_{rule.id}",
                    severity=rule.severity,
                    title=f"Monitoring Alert: {rule.name}",
                    description=(
                        f"Equipment '{equipment.name}' violated rule '{rule.name}': "
                        f"{rule.measurement_type} reached {val} {rule.unit} (threshold: {rule.threshold}). "
                        "Advisory only — verify before maintenance."
                    ),
                )

            detected_events.append(anomaly_event)

        db.commit()
        return detected_events

    # 2. Fallback Prototype Rules (if no custom rules configured)
    temp_crit = settings.anomaly_temperature_critical_c
    temp_warn = settings.anomaly_temperature_warning_c
    vib_crit = settings.anomaly_vibration_critical
    vib_warn = settings.anomaly_vibration_warning

    t_val = reading.temperature_c
    v_val = reading.vibration_value

    t_sev = None
    if t_val is not None:
        if t_val >= temp_crit:
            t_sev = Severity.CRITICAL
        elif t_val >= temp_warn:
            t_sev = Severity.MEDIUM

    v_sev = None
    if v_val is not None:
        if v_val >= vib_crit:
            v_sev = Severity.CRITICAL
        elif v_val >= vib_warn:
            v_sev = Severity.MEDIUM

    if t_sev is None and v_sev is None:
        alert_repo.close_open_anomalies(db, equipment_id=equipment.id, timestamp=reading.timestamp)
        db.commit()
        return []

    sev_order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}
    active_sevs = [s for s in (t_sev, v_sev) if s is not None]
    top_sev = max(active_sevs, key=lambda s: sev_order[s])

    if t_sev is not None and v_sev is not None:
        event_type = "combined_abnormality"
        title = "Combined Temperature and Vibration Anomaly"
    elif t_sev is not None:
        event_type = "high_temperature"
        title = "High Motor Temperature"
    else:
        event_type = "high_vibration"
        title = "High Motor Vibration"

    evidence = {
        "reading_id": str(reading.id),
        "temperature_c": t_val,
        "vibration_value": v_val,
        "thresholds": {
            "temp_warn": temp_warn,
            "temp_crit": temp_crit,
            "vib_warn": vib_warn,
            "vib_crit": vib_crit,
        },
        "disclaimer": "Default prototype threshold evaluation.",
    }

    open_anomaly = alert_repo.find_open_anomaly_event(
        db,
        equipment_id=equipment.id,
        event_type=event_type,
    )
    if open_anomaly:
        open_anomaly.end_timestamp = reading.timestamp
        open_anomaly.evidence_json = evidence
        open_anomaly.severity = top_sev.value
        anomaly_event = open_anomaly
    else:
        anomaly_event = alert_repo.create_anomaly_event(
            db,
            organization_id=equipment.organization_id,
            equipment_id=equipment.id,
            sensor_id=reading.sensor_id,
            event_type=event_type,
            severity=top_sev.value,
            summary=f"Prototype anomaly: {title}",
            start_timestamp=reading.timestamp,
            evidence_json=evidence,
        )

    open_alert = alert_repo.find_open_alert(
        db,
        equipment_id=equipment.id,
        alert_type=event_type,
    )
    if not open_alert:
        alert_repo.create_alert(
            db,
            organization_id=equipment.organization_id,
            equipment_id=equipment.id,
            anomaly_event_id=anomaly_event.id,
            alert_type=event_type,
            severity=top_sev.value,
            title=title,
            description="Generated from simulated data using prototype thresholds. Advisory only.",
        )

    detected_events.append(anomaly_event)
    db.commit()
    return detected_events


# ---------------------------------------------------------------------------
# Equipment Health & Overview
# ---------------------------------------------------------------------------


def get_equipment_status(
    db: Session,
    actor: User,
    equipment_id: uuid.UUID | str,
) -> EquipmentStatusResponse:
    equipment = eq_service.get_equipment(db, actor, equipment_id)

    from app.modules.sensors import reading_repository as r_repo
    latest = r_repo.get_latest_reading(db, equipment_id=equipment.id)

    now = utcnow()
    seconds_since_latest = (
        None if latest is None else max(0.0, (now - latest.timestamp).total_seconds())
    )
    is_stale = (
        latest is None
        or seconds_since_latest is None
        or seconds_since_latest > settings.stale_data_threshold_seconds
    )

    snapshot = None
    if latest is not None:
        snapshot = ReadingSnapshot(
            id=latest.id,
            timestamp=latest.timestamp,
            received_at=latest.received_at,
            temperature_c=latest.temperature_c,
            vibration_value=latest.vibration_value,
            vibration_unit=latest.vibration_unit,
            speed_rpm=latest.speed_rpm,
            load_percent=latest.load_percent,
            quality_status=latest.quality_status,
        )

    return EquipmentStatusResponse(
        equipment_id=equipment.id,
        name=equipment.name,
        status=equipment.status,
        latest_reading=snapshot,
        seconds_since_latest=seconds_since_latest,
        is_stale=is_stale,
        stale_threshold_seconds=settings.stale_data_threshold_seconds,
        open_alert_count=alert_repo.count_open_alerts(db, equipment_id=equipment.id),
    )


def get_overview(
    db: Session,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
) -> list[EquipmentStatusResponse]:
    target_org_id = None
    if organization_id:
        target_org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            target_org_id = memberships[0].organization_id

    equipment_list = eq_repo.list_equipment(
        db,
        organization_id=target_org_id,
        include_archived=False,
    )
    return [get_equipment_status(db, actor, item.id) for item in equipment_list]
