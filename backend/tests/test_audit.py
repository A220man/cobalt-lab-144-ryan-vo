import pytest
from httpx import AsyncClient, ASGITransport
import json

from app.main import create_app
from app.core.database import engine, Base, async_session_maker
from app.models.audit import CoverageUnit, Finding


@pytest.fixture
async def viewer_client(viewer_token: str):
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {viewer_token}"}
    ) as ac:
        yield ac


@pytest.fixture
async def operator_client(operator_token: str):
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {operator_token}"}
    ) as ac:
        yield ac


@pytest.fixture
async def admin_client(admin_token: str):
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {admin_token}"}
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_coverage_unit(operator_client: AsyncClient):
    response = await operator_client.post(
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
    return data["unit_id"]


@pytest.mark.asyncio
async def test_list_coverage_units(viewer_client: AsyncClient, operator_client: AsyncClient):
    # Create a unit first using operator
    await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-002",
            "title": "Coverage Unit 2",
            "attack_class": "injection",
        },
    )
    # List with viewer
    response = await viewer_client.get("/api/v1/audit/units")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(u["attack_class"] == "injection" for u in data)


@pytest.mark.asyncio
async def test_get_coverage_unit(viewer_client: AsyncClient, operator_client: AsyncClient):
    create_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-003",
            "title": "Get Test Unit",
            "attack_class": "crypto",
        },
    )
    unit_id = create_resp.json()["unit_id"]

    response = await viewer_client.get(f"/api/v1/audit/units/{unit_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Get Test Unit"
    assert data["unit_id"] == "CU-003"


@pytest.mark.asyncio
async def test_update_coverage_unit(operator_client: AsyncClient):
    create_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-004",
            "title": "Update Test Unit",
            "attack_class": "crypto",
        },
    )
    unit_id = create_resp.json()["unit_id"]

    response = await operator_client.patch(
        f"/api/v1/audit/units/{unit_id}",
        json={"title": "Updated Title", "status": "in_progress"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_progress"
    assert data["attack_class"] == "crypto"  # unchanged


@pytest.mark.asyncio
async def test_delete_coverage_unit(admin_client: AsyncClient, operator_client: AsyncClient):
    create_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-005",
            "title": "Delete Test Unit",
            "attack_class": "injection",
        },
    )
    unit_id = create_resp.json()["unit_id"]

    response = await admin_client.delete(f"/api/v1/audit/units/{unit_id}")
    assert response.status_code == 204

    # Verify deletion
    get_resp = await operator_client.get(f"/api/v1/audit/units/{unit_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_finding(operator_client: AsyncClient):
    # First create a coverage unit
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-006",
            "title": "Finding Test Unit",
            "attack_class": "injection",
        },
    )
    unit_id = unit_resp.json()["id"]

    response = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-001",
            "unit_id": unit_id,
            "title": "SQL Injection",
            "description": "User input directly concatenated into SQL query",
            "attack_class": "injection",
            "severity": "high",
            "evidence": '{"file": "src/auth.py", "line": 42}',
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["finding_id"] == "F-001"
    assert data["title"] == "SQL Injection"
    assert data["severity"] == "high"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_findings(viewer_client: AsyncClient, operator_client: AsyncClient):
    # Create a unit first
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-007",
            "title": "Finding List Unit",
            "attack_class": "auth-bypass",
        },
    )
    unit_id = unit_resp.json()["id"]

    # Create findings
    await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-002",
            "unit_id": unit_id,
            "title": "Auth Bypass 1",
            "description": "Missing auth check",
            "attack_class": "auth-bypass",
            "severity": "high",
        },
    )
    await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-003",
            "unit_id": unit_id,
            "title": "Auth Bypass 2",
            "description": "Missing auth check",
            "attack_class": "auth-bypass",
            "severity": "medium",
        },
    )

    # List with viewer
    response = await viewer_client.get("/api/v1/audit/findings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Filter findings for our unit only
    unit_findings = [f for f in data if f["unit_id"] == unit_id]
    assert len(unit_findings) >= 2
    assert all(f["attack_class"] == "auth-bypass" for f in unit_findings)


@pytest.mark.asyncio
async def test_get_finding(viewer_client: AsyncClient, operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-008",
            "title": "Get Finding Unit",
            "attack_class": "auth-bypass",
        },
    )
    unit_id = unit_resp.json()["id"]

    finding_resp = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-004",
            "unit_id": unit_id,
            "title": "Auth Bypass",
            "description": "Missing auth check",
            "attack_class": "auth-bypass",
            "severity": "high",
        },
    )
    finding_id = finding_resp.json()["finding_id"]

    response = await viewer_client.get(f"/api/v1/audit/findings/{finding_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Auth Bypass"
    assert data["finding_id"] == "F-004"


@pytest.mark.asyncio
async def test_update_finding(operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-009",
            "title": "Update Finding Unit",
            "attack_class": "crypto",
        },
    )
    unit_id = unit_resp.json()["id"]

    finding_resp = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-005",
            "unit_id": unit_id,
            "title": "Weak Crypto",
            "description": "Using MD5",
            "attack_class": "crypto",
            "severity": "medium",
        },
    )
    finding_id = finding_resp.json()["finding_id"]

    response = await operator_client.patch(
        f"/api/v1/audit/findings/{finding_id}",
        json={"title": "Weak Crypto - Updated", "severity": "high"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Weak Crypto - Updated"
    assert data["severity"] == "high"
    assert data["attack_class"] == "crypto"  # unchanged


@pytest.mark.asyncio
async def test_delete_finding(admin_client: AsyncClient, operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-010",
            "title": "Delete Finding Unit",
            "attack_class": "injection",
        },
    )
    unit_id = unit_resp.json()["id"]

    finding_resp = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-006",
            "unit_id": unit_id,
            "title": "To Delete",
            "description": "Will be deleted",
            "attack_class": "injection",
            "severity": "low",
        },
    )
    finding_id = finding_resp.json()["finding_id"]

    response = await admin_client.delete(f"/api/v1/audit/findings/{finding_id}")
    assert response.status_code == 204

    get_resp = await operator_client.get(f"/api/v1/audit/findings/{finding_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_export_coverage_ledger(viewer_client: AsyncClient, operator_client: AsyncClient):
    await operator_client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-011", "title": "Export Unit 1", "attack_class": "injection"},
    )
    await operator_client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-012", "title": "Export Unit 2", "attack_class": "crypto"},
    )

    response = await viewer_client.get("/api/v1/audit/export/coverage-ledger")
    assert response.status_code == 200
    data = response.json()
    assert "units" in data
    assert "total_units" in data
    assert "by_status" in data
    assert "by_attack_class" in data
    assert data["total_units"] >= 2


@pytest.mark.asyncio
async def test_export_findings(viewer_client: AsyncClient, operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-013", "title": "Export Finding Unit", "attack_class": "injection"},
    )
    unit_id = unit_resp.json()["id"]

    await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-007",
            "unit_id": unit_id,
            "title": "Export Finding",
            "description": "Test",
            "attack_class": "injection",
            "severity": "high",
        },
    )

    response = await viewer_client.get("/api/v1/audit/export/findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "total_findings" in data
    assert data["total_findings"] >= 1


@pytest.mark.asyncio
async def test_create_finding_preserved_uses(operator_client: AsyncClient):
    # First create a coverage unit
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-014",
            "title": "Preserved Uses Test Unit",
            "attack_class": "auth-bypass",
        },
    )
    unit_id = unit_resp.json()["id"]

    preserved_uses = [
        {"who": "plugin-author", "path": "POST /api/v1/plugins/{id}/execute", "how_it_keeps_working": "Plugin uses caller own stored credentials via consent flow"},
        {"who": "platform-admin", "path": "GET /api/v1/admin/audit", "how_it_keeps_working": "Admin API uses service account, unchanged"}
    ]
    
    response = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-008",
            "unit_id": unit_id,
            "title": "Credential Leakage",
            "description": "Plugin can access caller credentials",
            "attack_class": "auth-bypass",
            "severity": "high",
            "preserved_uses": json.dumps(preserved_uses),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["finding_id"] == "F-008"
    assert data["preserved_uses"] is not None
    # Verify the preserved_uses content
    parsed = json.loads(data["preserved_uses"])
    assert len(parsed) == 2
    assert parsed[0]["who"] == "plugin-author"
    assert parsed[1]["who"] == "platform-admin"


@pytest.mark.asyncio
async def test_update_finding_preserved_uses(operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={
            "unit_id": "CU-015",
            "title": "Update Preserved Uses Unit",
            "attack_class": "crypto",
        },
    )
    unit_id = unit_resp.json()["id"]

    finding_resp = await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-009",
            "unit_id": unit_id,
            "title": "Weak Crypto",
            "description": "Using MD5",
            "attack_class": "crypto",
            "severity": "medium",
        },
    )
    finding_id = finding_resp.json()["finding_id"]

    # Update with preserved_uses
    preserved_uses = [
        {"who": "legacy-client", "path": "GET /api/v1/legacy/data", "how_it_keeps_working": "Legacy clients use compatibility mode with explicit opt-in"}
    ]
    
    response = await operator_client.patch(
        f"/api/v1/audit/findings/{finding_id}",
        json={
            "title": "Weak Crypto - Updated",
            "preserved_uses": json.dumps(preserved_uses),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Weak Crypto - Updated"
    assert data["preserved_uses"] is not None
    parsed = json.loads(data["preserved_uses"])
    assert len(parsed) == 1
    assert parsed[0]["who"] == "legacy-client"


@pytest.mark.asyncio
async def test_export_findings_preserved_uses(viewer_client: AsyncClient, operator_client: AsyncClient):
    unit_resp = await operator_client.post(
        "/api/v1/audit/units",
        json={"unit_id": "CU-016", "title": "Export Preserved Uses Unit", "attack_class": "injection"},
    )
    unit_id = unit_resp.json()["id"]

    preserved_uses = [
        {"who": "api-consumer", "path": "POST /api/v1/data", "how_it_keeps_working": "API consumers use their own credentials via token exchange"}
    ]
    
    await operator_client.post(
        "/api/v1/audit/findings",
        json={
            "finding_id": "F-010",
            "unit_id": unit_id,
            "title": "Export Preserved Uses Finding",
            "description": "Test",
            "attack_class": "injection",
            "severity": "high",
            "preserved_uses": json.dumps(preserved_uses),
        },
    )

    response = await viewer_client.get("/api/v1/audit/export/findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert data["total_findings"] >= 1
    # Find our exported finding
    exported = next((f for f in data["findings"] if f["finding_id"] == "F-010"), None)
    assert exported is not None
    assert exported["preserved_uses"] is not None
    parsed = json.loads(exported["preserved_uses"])
    assert len(parsed) == 1
    assert parsed[0]["who"] == "api-consumer"
