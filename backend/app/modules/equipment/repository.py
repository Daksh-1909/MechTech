from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, Equipment
from app.models.enums import EquipmentStatus


def get_equipment(db: Session, equipment_id: str) -> Equipment | None:
    return db.get(Equipment, equipment_id)


def list_equipment(db: Session, *, include_archived: bool) -> list[Equipment]:
    statement = select(Equipment).order_by(Equipment.created_at.asc(), Equipment.id.asc())
    if not include_archived:
        statement = statement.where(Equipment.status != EquipmentStatus.ARCHIVED.value)
    return list(db.scalars(statement))


def get_component(db: Session, component_id: int) -> Component | None:
    return db.get(Component, component_id)


def list_components(db: Session, equipment_id: str) -> list[Component]:
    return list(
        db.scalars(
            select(Component)
            .where(Component.equipment_id == equipment_id)
            .order_by(Component.component_key.asc())
        )
    )


def get_component_by_key(
    db: Session,
    *,
    equipment_id: str,
    component_key: str,
) -> Component | None:
    return db.scalar(
        select(Component).where(
            Component.equipment_id == equipment_id,
            Component.component_key == component_key,
        )
    )
