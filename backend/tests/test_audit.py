import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.main import create_app
from app.core.database import engine, Base, async_session_maker
from app.models.audit import CoverageUnit, Finding


@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    # Import models to register them
    from app.models import audit  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_coverage_unit(client: AsyncClient):
    response = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-001",
            "title": "Test Coverage Unit",
            "description": "A test coverage unit",
            "attack_class": "injection",
            "target_files": '["src/auth.py", "src/api.py"]',
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["unit_id"] == "CU-001"
    assert data["title"] == "Test Coverage Unit"
    assert data["attack_class"] == "injection"
    assert data["status"] == "planned"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_coverage_units(client: AsyncClient):
    await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-002",
            "title": "Coverage Unit 2",
            "attack_class": "xss",
        },
    )
    await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-003",
            "title": "Coverage Unit 3",
            "attack_class": "injection",
        },
    )
    response = await client.get("/api/v1/audit/units")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Test filter by attack_class
    response = await client.get("/api/v1/audit/units?attack_class=injection")
    assert response.status_code == 200
    data = response.json()
    assert all(u["attack_class"] == "injection" for u in data)


@pytest.mark.asyncio
async def test_get_coverage_unit(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-004",
            "title": "Get Test Unit",
            "attack_class": "auth-bypass",
        },
    )
    unit_id = create_resp.json()["unit_id"]
    response = await client.get(f"/api/v1/audit/units/{unit_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["unit_id"] == unit_id
    assert data["title"] == "Get Test Unit"


@pytest.mark.asyncio
async def test_update_coverage_unit(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-005",
            "title": "Original Title",
            "attack_class": "crypto",
            "status": "planned",
        },
    )
    unit_id = create_resp.json()["unit_id"]
    response = await client.patch(
        f"/api/v1/audit/units/{unit_id}",
        json={"title": "Updated Title", "status": "in_progress"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_progress"
    assert data["attack_class"] == "crypto"  # unchanged


@pytest.mark.asyncio
async def test_delete_coverage_unit(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-006", "title": "To Delete", "attack_class": "idor"},
    )
    unit_id = create_resp.json()["unit_id"]
    response = await client.delete(f"/api/v1/audit/units/{unit_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/audit/units/{unit_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_finding(client: AsyncClient):
    # First create a coverage unit
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-FIND-001",
            "title": "Unit for Finding",
            "attack_class": "injection",
        },
    )
    unit_db_id = unit_resp.json()["id"]

    response = await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-001",
            "unit_id": unit_db_id,
            "title": "SQL Injection in Login",
            "description": "Unsanitized input in login form allows SQL injection",
            "attack_class": "injection",
            "severity": "high",
            "evidence": '{"file": "src/auth.py", "line": 42}',
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["finding_id"] == "FIND-001"
    assert data["title"] == "SQL Injection in Login"
    assert data["severity"] == "high"
    assert data["status"] == "planned"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_findings(client: AsyncClient):
    # Create a unit first
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-FIND-002",
            "title": "Unit for Findings List",
            "attack_class": "xss",
        },
    )
    unit_db_id = unit_resp.json()["id"]

    await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-002",
            "unit_id": unit_db_id,
            "title": "XSS in Search",
            "description": "Reflected XSS in search parameter",
            "attack_class": "xss",
            "severity": "medium",
        },
    )
    await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-003",
            "unit_id": unit_db_id,
            "title": "XSS in Comments",
            "description": "Stored XSS in comments",
            "attack_class": "xss",
            "severity": "high",
        },
    )
    response = await client.get("/api/v1/audit/findings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Test filter by attack_class
    response = await client.get("/api/v1/audit/findings?attack_class=xss")
    assert response.status_code == 200
    data = response.json()
    assert all(f["attack_class"] == "xss" for f in data)
    # Test filter by severity
    response = await client.get("/api/v1/audit/findings?severity=high")
    assert response.status_code == 200
    data = response.json()
    assert all(f["severity"] == "high" for f in data)


@pytest.mark.asyncio
async def test_get_finding(client: AsyncClient):
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-FIND-003",
            "title": "Unit for Get Finding",
            "attack_class": "auth-bypass",
        },
    )
    unit_db_id = unit_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-004",
            "unit_id": unit_db_id,
            "title": "Auth Bypass",
            "description": "Missing auth check",
            "attack_class": "auth-bypass",
            "severity": "critical",
        },
    )
    finding_id = create_resp.json()["finding_id"]
    response = await client.get(f"/api/v1/audit/findings/{finding_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["finding_id"] == finding_id
    assert data["title"] == "Auth Bypass"


@pytest.mark.asyncio
async def test_update_finding(client: AsyncClient):
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-FIND-004",
            "title": "Unit for Update Finding",
            "attack_class": "crypto",
        },
    )
    unit_db_id = unit_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-005",
            "unit_id": unit_db_id,
            "title": "Weak Crypto",
            "description": "MD5 used for passwords",
            "attack_class": "crypto",
            "severity": "high",
            "status": "planned",
        },
    )
    finding_id = create_resp.json()["finding_id"]
    response = await client.patch(
        f"/api/v1/audit/findings/{finding_id}",
        json={"status": "confirmed", "severity": "critical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["severity"] == "critical"
    assert data["title"] == "Weak Crypto"  # unchanged


@pytest.mark.asyncio
async def test_delete_finding(client: AsyncClient):
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-FIND-005",
            "title": "Unit for Delete Finding",
            "attack_class": "idor",
        },
    )
    unit_db_id = unit_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-006",
            "unit_id": unit_db_id,
            "title": "IDOR",
            "description": "Insecure direct object reference",
            "attack_class": "idor",
            "severity": "medium",
        },
    )
    finding_id = create_resp.json()["finding_id"]
    response = await client.delete(f"/api/v1/audit/findings/{finding_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/audit/findings/{finding_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_export_coverage_ledger(client: AsyncClient):
    await client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-EXPORT-001", "title": "Export Unit 1", "attack_class": "injection"},
    )
    await client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-EXPORT-002", "title": "Export Unit 2", "attack_class": "xss"},
    )
    response = await client.get("/api/v1/audit/export/coverage-ledger")
    assert response.status_code == 200
    data = response.json()
    assert "units" in data
    assert "total_units" in data
    assert "by_status" in data
    assert "by_attack_class" in data
    assert data["total_units"] >= 2


@pytest.mark.asyncio
async def test_export_findings(client: AsyncClient):
    unit_resp = await client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-EXPORT-FIND", "title": "Export Findings Unit", "attack_class": "injection"},
    )
    unit_db_id = unit_resp.json()["id"]

    await client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "FIND-EXPORT-001",
            "unit_id": unit_db_id,
            "title": "Export Finding 1",
            "description": "Desc",
            "attack_class": "injection",
            "severity": "high",
        },
    )
    response = await client.get("/api/v1/audit/export/findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "total_findings" in data
    assert "by_status" in data
    assert "by_attack_class" in data
    assert data["total_findings"] >= 1

