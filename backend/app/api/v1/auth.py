from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import (
    get_current_token_data,
    require_admin,
    TokenData,
)
from app.models.auth import User, UserRoleAssociation, UserRole
from app.schemas.auth import TokenResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


class OIDCConfigResponse(BaseModel):
    issuer_url: str
    client_id: str
    redirect_uri: str


@router.get("/config", response_model=OIDCConfigResponse)
async def get_oidc_config():
    """Get OIDC configuration for frontend."""
    return OIDCConfigResponse(
        issuer_url=settings.OIDC_ISSUER_URL,
        client_id=settings.OIDC_CLIENT_ID,
        redirect_uri=settings.OIDC_REDIRECT_URI,
    )


@router.get("/me", response_model=TokenData)
async def get_current_user(token_data: TokenData = Depends(get_current_token_data)):
    """Get current authenticated user info."""
    return token_data


@router.post("/sync-user", response_model=TokenData)
async def sync_user(
    token_data: TokenData = Depends(get_current_token_data),
    db: AsyncSession = Depends(get_db),
):
    """Sync user from Keycloak to local database."""
    # Check if user exists
    result = await db.execute(select(User).where(User.sub == token_data.sub))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            sub=token_data.sub,
            email=token_data.email,
            username=token_data.username,
            first_name=token_data.first_name,
            last_name=token_data.last_name,
            is_active=token_data.is_active,
        )
        db.add(user)
        await db.flush()

    # Update user info
    user.email = token_data.email
    user.username = token_data.username
    user.first_name = token_data.first_name
    user.last_name = token_data.last_name
    user.is_active = token_data.is_active
    user.updated_at = func.now()

    # Sync roles
    # First, remove old roles
    await db.execute(
        UserRoleAssociation.__table__.delete().where(UserRoleAssociation.user_id == user.id)
    )

    # Add new roles
    for role_str in token_data.roles:
        try:
            role = UserRole(role_str)
            db.add(UserRoleAssociation(user_id=user.id, role=role))
        except ValueError:
            # Ignore unknown roles
            pass

    await db.commit()
    await db.refresh(user)

    return token_data


@router.get("/users", response_model=list[TokenData])
async def list_users(
    token_data: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()

    return [
        TokenData(
            sub=user.sub,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=[assoc.role.value for assoc in user.roles],
            is_active=user.is_active,
        )
        for user in users
    ]


@router.post("/logout")
async def logout():
    """Logout endpoint - client should clear token."""
    return {"message": "Logged out successfully"}
