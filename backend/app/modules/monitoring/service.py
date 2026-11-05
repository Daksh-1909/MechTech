from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.time import utcnow
from app.models import Alert, AnomalyEvent, Equipment, SensorReading
from app.models.enums import AlertStatus, Severity
from app.modules.equipment import repository as equipment_repository
from app.modules.monitoring.schemas import (
    EquipmentStatusResponse,
    ReadingSnapshot,
)

_OPEN_ALERT_STATUSES = (AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value)


def _warning_severity(
    value: float | None,
    *,
    warning: float,
    critical: float,
) -> Severity | None:
    if value is None:
        return None
    if value >= critical:
        return Severity.CRITICAL
    if value >= warning:
        return Severity.MEDIUM
    return None


def _max_severity(left: Severity | None, right: Severity | None) -> Severity | None:
    order = {
        Severity.LOW: 0,
        Severity.MEDIUM: 1,
        Severity.HIGH: 2,
        Severity.CRITICAL: 3,
    }
    candidates = [item for item in (left, right) if item is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda item: order[item])


def _find_open_anomaly(db: Session, equipment_id: str, event_type: str) -> AnomalyEvent | None:
    return db.scalar(
        select(AnomalyEvent)
        .where(
            AnomalyEvent.equipment_id == equipment_id,
            AnomalyEvent.event_type == event_type,
            AnomalyEvent.end_timestamp.is_(None),
        )
        .order_by(AnomalyEvent.start_timestamp.desc())
        .limit(1)
    )


def _find_open_alert(db: Session, equipment_id: str, alert_type: str) -> Alert | None:
    return db.scalar(
        select(Alert)
        .where(
            Alert.equipment_id == equipment_id,
            Alert.alert_type == alert_type,
            Alert.status.in_(_OPEN_ALERT_STATUSES),
        )
        .order_by(Alert.created_at.desc())
        .limit(1)
    )


def _reading_evidence(reading: SensorReading) -> dict:
    return {
        "reading_id": reading.id,
        "temperature_c": reading.temperature_c,
        "vibration_value": reading.vibration_value,
        "vibration_unit": reading.vibration_unit,
        "thresholds": {
            "temperature_warning_c": settings.anomaly_temperature_warning_c,
            "temperature_critical_c": settings.anomaly_temperature_critical_c,
            "vibration_warning": settings.anomaly_vibration_warning,
            "vibration_critical": settings.anomaly_vibration_critical,
        },
        "note": "Prototype thresholds, not industrial safety limits.",
    }


def _close_open_anomalies(db: Session, *, equipment_id: str, timestamp: datetime) -> None:
    events = db.scalars(
        select(AnomalyEvent).where(
            AnomalyEvent.equipment_id == equipment_id,
            AnomalyEvent.end_timestamp.is_(None),
        )
    )
    for event in events:
        event.end_timestamp = timestamp


def evaluate_reading(db: Session, reading: SensorReading) -> AnomalyEvent | None:
    temperature_severity = _warning_severity(
        reading.temperature_c,
        warning=settings.anomaly_temperature_warning_c,
        critical=settings.anomaly_temperature_critical_c,
    )
    vibration_severity = _warning_severity(
        reading.vibration_value,
        warning=settings.anomaly_vibration_warning,
        critical=settings.anomaly_vibration_critical,
    )

    if temperature_severity is None and vibration_severity is None:
        _close_open_anomalies(db, equipment_id=reading.equipment_id, timestamp=reading.timestamp)
        db.commit()
        return None

    if temperature_severity is not None and vibration_severity is not None:
        event_type = "combined_anomaly"
        severity = _max_severity(temperature_severity, vibration_severity)
        title = "Combined temperature and vibration anomaly"
    elif temperature_severity is not None:
        event_type = "high_temperature"
        severity = temperature_severity
        title = "High motor temperature"
    else:
        event_type = "high_vibration"
        severity = vibration_severity
        title = "High motor vibration"

    assert severity is not None
    evidence = _reading_evidence(reading)

    open_event = _find_open_anomaly(db, reading.equipment_id, event_type)
    if open_event is not None:
        open_event.end_timestamp = reading.timestamp
        open_event.evidence_json = evidence
        open_event.severity = severity.value
        anomaly_event = open_event
    else:
        anomaly_event = AnomalyEvent(
            equipment_id=reading.equipment_id,
            event_type=event_type,
            severity=severity.value,
            start_timestamp=reading.timestamp,
            end_timestamp=None,
            description=f"Prototype rule-based anomaly from reading {reading.id}.",
            evidence_json=evidence,
            anomaly_score=max(
                (reading.temperature_c or 0.0) / settings.anomaly_temperature_warning_c,
                (reading.vibration_value or 0.0) / settings.anomaly_vibration_warning,
            ),
        )
        db.add(anomaly_event)
        db.flush()

    if _find_open_alert(db, reading.equipment_id, event_type) is None:
        db.add(
            Alert(
                equipment_id=reading.equipment_id,
                anomaly_event_id=anomaly_event.id,
                alert_type=event_type,
                severity=severity.value,
                title=title,
                description=(
                    "Generated from simulated data using prototype thresholds. "
                    "Not a confirmed diagnosis."
                ),
            )
        )

    db.commit()
    return anomaly_event


def _open_alert_count(db: Session, equipment_id: str) -> int:
    count = db.scalar(
        select(func.count())
        .select_from(Alert)
        .where(
            Alert.equipment_id == equipment_id,
            Alert.status.in_(_OPEN_ALERT_STATUSES),
        )
    )
    return int(count or 0)


def _status_snapshot(db: Session, equipment: Equipment) -> EquipmentStatusResponse:
    latest = db.scalar(
        select(SensorReading)
        .where(SensorReading.equipment_id == equipment.id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(1)
    )

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
        open_alert_count=_open_alert_count(db, equipment.id),
    )


def get_equipment_status(db: Session, equipment_id: str) -> EquipmentStatusResponse:
    equipment = equipment_repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return _status_snapshot(db, equipment)


def get_overview(db: Session) -> list[EquipmentStatusResponse]:
    equipment = equipment_repository.list_equipment(db, include_archived=False)
    return [_status_snapshot(db, item) for item in equipment]
