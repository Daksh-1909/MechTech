"""Repository for AnomalyEvent and Alert queries and state transitions."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models.anomaly import Alert, AnomalyEvent
from app.models.enums import AlertStatus, ReviewStatus, Severity


_OPEN_ALERT_STATUSES = (AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value)


# ---------------------------------------------------------------------------
# Anomaly Events
# ---------------------------------------------------------------------------


def create_anomaly_event(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    event_type: str,
    severity: str,
    start_timestamp: datetime,
    rule_id: uuid.UUID | None = None,
    sensor_id: uuid.UUID | None = None,
    component_id: uuid.UUID | None = None,
    detector_name: str | None = None,
    model_version: str | None = None,
    summary: str | None = None,
    end_timestamp: datetime | None = None,
    anomaly_score: float | None = None,
    description: str | None = None,
    evidence_json: dict[str, Any] | None = None,
    status: str = "detected",
    review_status: str = ReviewStatus.PENDING.value,
) -> AnomalyEvent:
    event = AnomalyEvent(
        organization_id=organization_id,
        equipment_id=equipment_id,
        rule_id=rule_id,
        sensor_id=sensor_id,
        component_id=component_id,
        detector_name=detector_name,
        model_version=model_version,
        event_type=event_type,
        severity=severity,
        summary=summary,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        anomaly_score=anomaly_score,
        description=description,
        evidence_json=evidence_json,
        status=status,
        review_status=review_status,
        created_at=utcnow(),
    )
    db.add(event)
    db.flush()
    return event


def get_anomaly_event_by_id(db: Session, event_id: uuid.UUID | str) -> AnomalyEvent | None:
    eid = event_id if isinstance(event_id, uuid.UUID) else uuid.UUID(str(event_id))
    return db.scalar(
        select(AnomalyEvent)
        .options(
            joinedload(AnomalyEvent.equipment),
            joinedload(AnomalyEvent.rule),
            joinedload(AnomalyEvent.sensor),
            joinedload(AnomalyEvent.component),
            joinedload(AnomalyEvent.alerts),
        )
        .where(AnomalyEvent.id == eid)
    )


def find_open_anomaly_event(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    event_type: str | None = None,
    rule_id: uuid.UUID | None = None,
) -> AnomalyEvent | None:
    stmt = (
        select(AnomalyEvent)
        .where(
            AnomalyEvent.equipment_id == equipment_id,
            AnomalyEvent.end_timestamp.is_(None),
        )
        .order_by(AnomalyEvent.start_timestamp.desc())
        .limit(1)
    )
    if event_type is not None:
        stmt = stmt.where(AnomalyEvent.event_type == event_type)
    if rule_id is not None:
        stmt = stmt.where(AnomalyEvent.rule_id == rule_id)
    return db.scalar(stmt)


def close_open_anomalies(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    timestamp: datetime,
) -> int:
    events = list(
        db.scalars(
            select(AnomalyEvent).where(
                AnomalyEvent.equipment_id == equipment_id,
                AnomalyEvent.end_timestamp.is_(None),
            )
        )
    )
    for ev in events:
        ev.end_timestamp = timestamp
        ev.status = "resolved"
    db.flush()
    return len(events)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def create_alert(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    alert_type: str,
    severity: str,
    title: str,
    description: str | None = None,
    anomaly_event_id: uuid.UUID | None = None,
    status: str = AlertStatus.OPEN.value,
) -> Alert:
    alert = Alert(
        organization_id=organization_id,
        equipment_id=equipment_id,
        anomaly_event_id=anomaly_event_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        status=status,
        created_at=utcnow(),
    )
    db.add(alert)
    db.flush()
    return alert


def get_alert_by_id(db: Session, alert_id: uuid.UUID | str) -> Alert | None:
    aid = alert_id if isinstance(alert_id, uuid.UUID) else uuid.UUID(str(alert_id))
    return db.scalar(
        select(Alert)
        .options(
            joinedload(Alert.equipment),
            joinedload(Alert.anomaly_event),
            joinedload(Alert.acknowledger),
            joinedload(Alert.resolver),
        )
        .where(Alert.id == aid)
    )


def find_open_alert(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    alert_type: str | None = None,
    anomaly_event_id: uuid.UUID | None = None,
) -> Alert | None:
    stmt = (
        select(Alert)
        .where(
            Alert.equipment_id == equipment_id,
            Alert.status.in_(_OPEN_ALERT_STATUSES),
        )
        .order_by(Alert.created_at.desc())
        .limit(1)
    )
    if alert_type is not None:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if anomaly_event_id is not None:
        stmt = stmt.where(Alert.anomaly_event_id == anomaly_event_id)
    return db.scalar(stmt)


def list_alerts(
    db: Session,
    *,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Alert]:
    stmt = (
        select(Alert)
        .options(
            joinedload(Alert.equipment),
            joinedload(Alert.anomaly_event),
        )
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if organization_id is not None:
        oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(Alert.organization_id == oid)
    if equipment_id is not None:
        eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
        stmt = stmt.where(Alert.equipment_id == eid)
    if status is not None:
        stmt = stmt.where(Alert.status == status)
    if severity is not None:
        stmt = stmt.where(Alert.severity == severity)

    return list(db.scalars(stmt))


def update_alert_status(
    db: Session,
    *,
    alert_id: uuid.UUID | str,
    new_status: str,
    actor_id: uuid.UUID | None = None,
    note: str | None = None,
) -> Alert | None:
    aid = alert_id if isinstance(alert_id, uuid.UUID) else uuid.UUID(str(alert_id))
    alert = db.get(Alert, aid)
    if not alert:
        return None

    now = utcnow()
    alert.status = new_status
    if new_status == AlertStatus.ACKNOWLEDGED.value:
        alert.acknowledged_at = now
        alert.acknowledged_by = actor_id
    elif new_status in (AlertStatus.RESOLVED.value, AlertStatus.DISMISSED.value):
        alert.resolved_at = now
        alert.resolved_by = actor_id
        if note:
            alert.resolution_note = note

    db.flush()
    return alert


def count_open_alerts(
    db: Session,
    *,
    equipment_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
) -> int:
    stmt = select(func.count(Alert.id)).where(Alert.status.in_(_OPEN_ALERT_STATUSES))
    if equipment_id is not None:
        stmt = stmt.where(Alert.equipment_id == equipment_id)
    if organization_id is not None:
        stmt = stmt.where(Alert.organization_id == organization_id)
    return int(db.scalar(stmt) or 0)
