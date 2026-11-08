import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.core.database import engine, Base, async_session_maker
from app.models.item import Item


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
async def test_create_item(operator_client: AsyncClient):
    response = await operator_client.post(
        "/api/v1/items", 
        json={"name": "Test Item", "description": "A test item"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_items(viewer_client: AsyncClient, operator_client: AsyncClient):
    await operator_client.post("/api/v1/items", json={"name": "Item 1"})
    await operator_client.post("/api/v1/items", json={"name": "Item 2"})

    response = await viewer_client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_item(viewer_client: AsyncClient, operator_client: AsyncClient):
    create_resp = await operator_client.post("/api/v1/items", json={"name": "Get Item"})
    item_id = create_resp.json()["id"]

    response = await viewer_client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Item"
    assert data["id"] == item_id


@pytest.mark.asyncio
async def test_update_item(operator_client: AsyncClient):
    create_resp = await operator_client.post("/api/v1/items", json={"name": "Update Item"})
    item_id = create_resp.json()["id"]

    response = await operator_client.patch(
        f"/api/v1/items/{item_id}", 
        json={"name": "Updated Item", "description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_item(admin_client: AsyncClient, operator_client: AsyncClient):
    create_resp = await operator_client.post("/api/v1/items", json={"name": "Delete Item"})
    item_id = create_resp.json()["id"]

    response = await admin_client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204

    get_resp = await operator_client.get(f"/api/v1/items/{item_id}")
    assert get_resp.status_code == 404
