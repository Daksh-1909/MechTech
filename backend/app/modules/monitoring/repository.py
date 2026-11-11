"""Repository for MonitoringRule persistence and queries."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models.monitoring_rule import MonitoringRule


def create_rule(
    db: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    measurement_type: str,
    operator: str,
    threshold: float,
    unit: str,
    created_by: uuid.UUID,
    equipment_type_id: uuid.UUID | None = None,
    duration_seconds: int = 0,
    severity: str = "medium",
    is_enabled: bool = True,
) -> MonitoringRule:
    rule = MonitoringRule(
        organization_id=organization_id,
        equipment_type_id=equipment_type_id,
        name=name.strip(),
        measurement_type=measurement_type.strip().lower(),
        operator=operator.strip().lower(),
        threshold=threshold,
        unit=unit.strip(),
        duration_seconds=duration_seconds,
        severity=severity.strip().lower(),
        is_enabled=is_enabled,
        version=1,
        created_by=created_by,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(rule)
    db.flush()
    return rule


def get_rule_by_id(db: Session, rule_id: uuid.UUID | str) -> MonitoringRule | None:
    rid = rule_id if isinstance(rule_id, uuid.UUID) else uuid.UUID(str(rule_id))
    return db.scalar(
        select(MonitoringRule)
        .options(
            joinedload(MonitoringRule.organization),
            joinedload(MonitoringRule.equipment_type),
            joinedload(MonitoringRule.creator),
        )
        .where(MonitoringRule.id == rid)
    )


def list_rules(
    db: Session,
    *,
    organization_id: uuid.UUID | str | None = None,
    equipment_type_id: uuid.UUID | str | None = None,
    measurement_type: str | None = None,
    is_enabled: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MonitoringRule]:
    stmt = (
        select(MonitoringRule)
        .options(
            joinedload(MonitoringRule.equipment_type),
            joinedload(MonitoringRule.creator),
        )
        .order_by(MonitoringRule.created_at.desc(), MonitoringRule.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if organization_id is not None:
        oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(MonitoringRule.organization_id == oid)
    if equipment_type_id is not None:
        etid = equipment_type_id if isinstance(equipment_type_id, uuid.UUID) else uuid.UUID(str(equipment_type_id))
        stmt = stmt.where(MonitoringRule.equipment_type_id == etid)
    if measurement_type is not None:
        stmt = stmt.where(MonitoringRule.measurement_type == measurement_type.strip().lower())
    if is_enabled is not None:
        stmt = stmt.where(MonitoringRule.is_enabled == is_enabled)

    return list(db.scalars(stmt))


def get_active_rules_for_equipment(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_type_id: uuid.UUID | None,
) -> list[MonitoringRule]:
    """Fetch enabled rules applying to this equipment (matching equipment_type or generic to org)."""
    type_condition = MonitoringRule.equipment_type_id.is_(None)
    if equipment_type_id is not None:
        type_condition = or_(type_condition, MonitoringRule.equipment_type_id == equipment_type_id)

    stmt = select(MonitoringRule).where(
        MonitoringRule.organization_id == organization_id,
        MonitoringRule.is_enabled.is_(True),
        type_condition,
    )
    return list(db.scalars(stmt))


def update_rule(
    db: Session,
    *,
    rule_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> MonitoringRule | None:
    rid = rule_id if isinstance(rule_id, uuid.UUID) else uuid.UUID(str(rule_id))
    rule = db.get(MonitoringRule, rid)
    if not rule:
        return None

    for field, value in changes.items():
        if hasattr(rule, field) and field not in {"id", "organization_id", "created_by", "created_at"}:
            setattr(rule, field, value)
    rule.version += 1
    rule.updated_at = utcnow()
    db.flush()
    return rule


def delete_rule(db: Session, rule_id: uuid.UUID | str) -> bool:
    rid = rule_id if isinstance(rule_id, uuid.UUID) else uuid.UUID(str(rule_id))
    rule = db.get(MonitoringRule, rid)
    if not rule:
        return False
    db.delete(rule)
    db.flush()
    return True

