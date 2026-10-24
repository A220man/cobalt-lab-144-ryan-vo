import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.main import create_app
from app.core.database import engine, Base, async_session_maker
from app.models.item import Item


@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    # Import models to register them
    from app.models import item  # noqa: F401
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
async def test_create_item(client: AsyncClient):
    response = await client.post("/api/v1/items", json={"name": "Test Item", "description": "A test item"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient):
    await client.post("/api/v1/items", json={"name": "Item 1"})
    await client.post("/api/v1/items", json={"name": "Item 2"})
    response = await client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_item(client: AsyncClient):
    create_resp = await client.post("/api/v1/items", json={"name": "Get Test"})
    item_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test"
    assert data["id"] == item_id


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    create_resp = await client.post("/api/v1/items", json={"name": "Original", "description": "Old"})
    item_id = create_resp.json()["id"]
    response = await client.patch(f"/api/v1/items/{item_id}", json={"name": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Old"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    create_resp = await client.post("/api/v1/items", json={"name": "To Delete"})
    item_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/items/{item_id}")
    assert get_resp.status_code == 404
