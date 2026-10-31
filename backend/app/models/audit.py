from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class UnitStatus(str, PyEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DEFERRED = "deferred"
    COMPLETED = "completed"


class FindingStatus(str, PyEnum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    NEEDS_VALIDATION = "needs_validation"
    REJECTED = "rejected"


class Severity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CoverageUnit(Base):
    __tablename__ = "coverage_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attack_class = Column(String(64), nullable=False, index=True)
    target_files = Column(Text, nullable=True)  # JSON array of file paths
    status = Column(SQLEnum(UnitStatus), default=UnitStatus.PLANNED, nullable=False, index=True)
    assigned_hunter = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    findings = relationship("Finding", back_populates="unit", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_coverage_units_attack_class_status", "attack_class", "status"),
    )


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(String(64), unique=True, nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("coverage_units.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    attack_class = Column(String(64), nullable=False, index=True)
    severity = Column(SQLEnum(Severity), default=Severity.INFO, nullable=False)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.PLANNED, nullable=False, index=True)
    evidence = Column(Text, nullable=True)  # JSON serialized evidence
    remediation = Column(Text, nullable=True)  # JSON serialized remediation
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    unit = relationship("CoverageUnit", back_populates="findings")

    __table_args__ = (
        Index("ix_findings_attack_class_status", "attack_class", "status"),
    )
