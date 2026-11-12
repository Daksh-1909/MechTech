from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import DiagnosisStatus, EvidenceType, INTEGRITY_CHECKS, ReviewStatus, Severity

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.fault import Fault
    from app.models.organization import Organization
    from app.models.user import User


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_diagnoses_status"], name="ck_diagnoses_status"),
        Index("ix_diagnoses_org_status_generated", "organization_id", "status", "generated_at"),
        Index("ix_diagnoses_equipment_generated", "equipment_id", "generated_at"),
        Index("ix_diagnoses_fault", "primary_fault_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    primary_fault_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("faults.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=DiagnosisStatus.POSSIBLE_FAULT.value,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Severity.MEDIUM.value,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    diagnostic_policy_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    generated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    # Human review workflow
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship()
    primary_fault: Mapped["Fault | None"] = relationship()
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])
    evidence_items: Mapped[list["DiagnosisEvidence"]] = relationship(
        back_populates="diagnosis",
        cascade="all, delete-orphan",
    )


class DiagnosisEvidence(Base):
    __tablename__ = "diagnosis_evidence"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_diagnosis_evidence_type"],
            name="ck_diagnosis_evidence_type",
        ),
        Index("ix_diagnosis_evidence_diagnosis", "diagnosis_id"),
        Index("ix_diagnosis_evidence_type", "evidence_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    diagnosis_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("diagnoses.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(150), nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    diagnosis: Mapped["Diagnosis"] = relationship(back_populates="evidence_items")

