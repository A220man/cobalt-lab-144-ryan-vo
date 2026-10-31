from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class UnitStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DEFERRED = "deferred"
    COMPLETED = "completed"


class FindingStatus(str, Enum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    NEEDS_VALIDATION = "needs_validation"
    REJECTED = "rejected"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CoverageUnitBase(BaseModel):
    unit_id: str
    title: str
    description: Optional[str] = None
    attack_class: str
    target_files: Optional[str] = None


class CoverageUnitCreate(CoverageUnitBase):
    pass


class CoverageUnitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    attack_class: Optional[str] = None
    target_files: Optional[str] = None
    status: Optional[UnitStatus] = None
    assigned_hunter: Optional[str] = None


class CoverageUnitRead(CoverageUnitBase):
    id: int
    status: UnitStatus
    assigned_hunter: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime) -> str:
        return dt.isoformat()


class FindingBase(BaseModel):
    finding_id: str
    unit_id: int
    title: str
    description: str
    attack_class: str
    severity: Severity = Severity.INFO


class FindingCreate(FindingBase):
    pass


class FindingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    attack_class: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[FindingStatus] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None


class FindingRead(FindingBase):
    id: int
    status: FindingStatus
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at', 'verified_at')
    def serialize_dt(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None


class CoverageLedgerExport(BaseModel):
    units: List[CoverageUnitRead]
    generated_at: datetime
    total_units: int
    by_status: Dict[str, int]
    by_attack_class: Dict[str, int]


class FindingsExport(BaseModel):
    findings: List[FindingRead]
    generated_at: datetime
    total_findings: int
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    by_attack_class: Dict[str, int]
