import pytest
from httpx import AsyncClient, ASGITransport
import jwt
from datetime import datetime, timedelta, timezone

from app.main import create_app
from app.core.database import engine, Base, async_session_maker
from app.core.config import settings


# Test secret for JWT signing
TEST_SECRET = "test-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"


def create_test_token(sub: str = "test-user", roles: list = None, exp_minutes: int = 30) -> str:
    """Create a test JWT token."""
    if roles is None:
        roles = ["viewer"]
    payload = {
        "sub": sub,
        "email": "test@example.com",
        "preferred_username": "testuser",
        "given_name": "Test",
        "family_name": "User",
        "realm_access": {"roles": roles},
        "resource_access": {settings.OIDC_CLIENT_ID: {"roles": roles}} if settings.OIDC_CLIENT_ID else {},
        "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutes),
        "iat": datetime.now(timezone.utc),
        "iss": settings.OIDC_ISSUER_URL or "http://localhost:8080/realms/cobalt-lab",
        "aud": settings.OIDC_CLIENT_ID or "cobalt-lab",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def viewer_token():
    return create_test_token(roles=["viewer"])


@pytest.fixture
def operator_token():
    return create_test_token(roles=["operator"])


@pytest.fixture
def admin_token():
    return create_test_token(roles=["admin"])


@pytest.fixture(scope="session")
def app():
    """Shared app instance for all tests."""
    return create_app()


@pytest.fixture
async def client(app):
    """Base client without authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def viewer_client(app, viewer_token):
    """Client with viewer authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {viewer_token}"}
    ) as ac:
        yield ac


@pytest.fixture
async def operator_client(app, operator_token):
    """Client with operator authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {operator_token}"}
    ) as ac:
        yield ac


@pytest.fixture
async def admin_client(app, admin_token):
    """Client with admin authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {admin_token}"}
    ) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def init_test_db(app):
    # Import models to register them
    from app.models import audit, auth, item  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
