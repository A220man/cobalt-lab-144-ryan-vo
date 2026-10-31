from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import List, Dict

from app.core.database import get_db
from app.models.audit import CoverageUnit, Finding, UnitStatus, FindingStatus, Severity
from app.schemas.audit import (
    CoverageUnitCreate, CoverageUnitUpdate, CoverageUnitRead,
    FindingCreate, FindingUpdate, FindingRead,
    CoverageLedgerExport, FindingsExport
)

router = APIRouter(prefix="/audit", tags=["audit"])

# Coverage Unit endpoints

@router.post("/units", response_model=CoverageUnitRead, status_code=status.HTTP_201_CREATED)
async def create_coverage_unit(unit_in: CoverageUnitCreate, db: AsyncSession = Depends(get_db)):
    unit = CoverageUnit(**unit_in.model_dump())
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


@router.get("/units", response_model=List[CoverageUnitRead])
async def list_coverage_units(
    skip: int = 0, limit: int = 100, attack_class: str = None, status: UnitStatus = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(CoverageUnit)
    if attack_class:
        query = query.where(CoverageUnit.attack_class == attack_class)
    if status:
        query = query.where(CoverageUnit.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/units/{unit_id}", response_model=CoverageUnitRead)
async def get_coverage_unit(unit_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageUnit).where(CoverageUnit.unit_id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Coverage unit not found")
    return unit


@router.patch("/units/{unit_id}", response_model=CoverageUnitRead)
async def update_coverage_unit(unit_id: str, unit_in: CoverageUnitUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageUnit).where(CoverageUnit.unit_id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Coverage unit not found")
    for field, value in unit_in.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    await db.commit()
    await db.refresh(unit)
    return unit


@router.delete("/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coverage_unit(unit_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageUnit).where(CoverageUnit.unit_id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Coverage unit not found")
    await db.delete(unit)
    await db.commit()
    return None

# Finding endpoints

@router.post("/findings", response_model=FindingRead, status_code=status.HTTP_201_CREATED)
async def create_finding(finding_in: FindingCreate, db: AsyncSession = Depends(get_db)):
    finding = Finding(**finding_in.model_dump())
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.get("/findings", response_model=List[FindingRead])
async def list_findings(
    skip: int = 0, limit: int = 100, attack_class: str = None, 
    finding_status: FindingStatus = None, severity: Severity = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Finding)
    if attack_class:
        query = query.where(Finding.attack_class == attack_class)
    if finding_status:
        query = query.where(Finding.status == finding_status)
    if severity:
        query = query.where(Finding.severity == severity)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/findings/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch("/findings/{finding_id}", response_model=FindingRead)
async def update_finding(finding_id: str, finding_in: FindingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    for field, value in finding_in.model_dump(exclude_unset=True).items():
        setattr(finding, field, value)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.delete("/findings/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
    return None

# Export endpoints

@router.get("/export/coverage-ledger", response_model=CoverageLedgerExport)
async def export_coverage_ledger(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageUnit))
    units = result.scalars().all()
    
    by_status: Dict[str, int] = {}
    by_attack_class: Dict[str, int] = {}
    
    for unit in units:
        by_status[unit.status.value] = by_status.get(unit.status.value, 0) + 1
        by_attack_class[unit.attack_class] = by_attack_class.get(unit.attack_class, 0) + 1
    
    return CoverageLedgerExport(
        units=units,
        generated_at=datetime.utcnow(),
        total_units=len(units),
        by_status=by_status,
        by_attack_class=by_attack_class
    )


@router.get("/export/findings", response_model=FindingsExport)
async def export_findings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding))
    findings = result.scalars().all()
    
    by_status: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    by_attack_class: Dict[str, int] = {}
    
    for finding in findings:
        by_status[finding.status.value] = by_status.get(finding.status.value, 0) + 1
        by_severity[finding.severity.value] = by_severity.get(finding.severity.value, 0) + 1
        by_attack_class[finding.attack_class] = by_attack_class.get(finding.attack_class, 0) + 1
    
    return FindingsExport(
        findings=findings,
        generated_at=datetime.utcnow(),
        total_findings=len(findings),
        by_status=by_status,
        by_severity=by_severity,
        by_attack_class=by_attack_class
    )
