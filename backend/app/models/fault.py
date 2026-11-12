from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, UTCDateTime
from app.models.enums import Severity

if TYPE_CHECKING:
    from app.models.equipment import EquipmentType


class Fault(Base):
    __tablename__ = "faults"
    __table_args__ = (
        Index("ix_faults_key", "key", unique=True),
        Index("ix_faults_eq_type", "equipment_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_type_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("equipment_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    default_severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Severity.MEDIUM.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment_type: Mapped["EquipmentType | None"] = relationship()

