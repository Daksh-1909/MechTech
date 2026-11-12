from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, NodeType

if TYPE_CHECKING:
    from app.models.equipment import EquipmentType


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    __table_args__ = (
        UniqueConstraint("key", name="uq_knowledge_nodes_key"),
        CheckConstraint(
            INTEGRITY_CHECKS["ck_knowledge_node_type"],
            name="ck_knowledge_node_type",
        ),
        Index("ix_knowledge_nodes_node_type", "node_type"),
        Index("ix_knowledge_nodes_eq_type", "equipment_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    node_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=NodeType.FAULT.value,
    )
    key: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_type_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("equipment_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    attributes_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
    )

    equipment_type: Mapped["EquipmentType | None"] = relationship()

    # Backwards compatibility property
    @property
    def stable_key(self) -> str:
        return self.key


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_knowledge_edge_type"],
            name="ck_knowledge_edge_type",
        ),
        Index("ix_knowledge_edges_source", "source_node_id"),
        Index("ix_knowledge_edges_target", "target_node_id"),
        Index("ix_knowledge_edges_type", "relationship_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    source_node: Mapped["KnowledgeNode"] = relationship(foreign_keys=[source_node_id])
    target_node: Mapped["KnowledgeNode"] = relationship(foreign_keys=[target_node_id])
