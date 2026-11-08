from datetime import datetime, timedelta
from typing import Optional, List
from functools import lru_cache
import os

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.auth import TokenData, UserRole


class JWTPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    realm_access: Optional[dict] = None
    resource_access: Optional[dict] = None
    exp: int
    iat: int
    iss: str
    aud: Optional[str] = None


security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    """Get JWKS client for Keycloak public keys."""
    if not settings.OIDC_ISSUER_URL:
        raise ValueError("OIDC_ISSUER_URL not configured")
    jwks_url = f"{settings.OIDC_ISSUER_URL}/protocol/openid-connect/certs"
    return PyJWKClient(jwks_url)


def is_test_environment() -> bool:
    """Check if running in test environment."""
    return (
        settings.DEBUG 
        or settings.SECRET_KEY == "dev-secret-change-in-production"
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
        or os.environ.get("TESTING") == "1"
    )


def decode_token(token: str) -> JWTPayload:
    """Decode and validate JWT token using Keycloak JWKS or test secret."""
    # Test mode: use HS256 with test secret
    if is_test_environment():
        try:
            payload = jwt.decode(
                token,
                "test-secret-key-for-testing-only",
                algorithms=["HS256"],
                audience=settings.OIDC_CLIENT_ID or "cobalt-lab",
                issuer=settings.OIDC_ISSUER_URL or "http://localhost:8080/realms/cobalt-lab",
                options={"verify_aud": bool(settings.OIDC_CLIENT_ID)}
            )
            return JWTPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Production mode: use RS256 with Keycloak JWKS
    if not settings.OIDC_ISSUER_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC not configured"
        )

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER_URL,
            options={"verify_aud": bool(settings.OIDC_CLIENT_ID)}
        )
        return JWTPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_roles(payload: JWTPayload) -> List[str]:
    """Extract roles from Keycloak token payload."""
    roles = []

    # Realm roles
    if payload.realm_access and "roles" in payload.realm_access:
        roles.extend(payload.realm_access["roles"])

    # Client roles
    if payload.resource_access and settings.OIDC_CLIENT_ID in payload.resource_access:
        client_roles = payload.resource_access[settings.OIDC_CLIENT_ID].get("roles", [])
        roles.extend(client_roles)

    return roles


def payload_to_token_data(payload: JWTPayload) -> TokenData:
    """Convert JWT payload to TokenData."""
    roles = extract_roles(payload)
    return TokenData(
        sub=payload.sub,
        email=payload.email,
        username=payload.preferred_username,
        first_name=payload.given_name,
        last_name=payload.family_name,
        roles=roles,
        is_active=True,
    )


async def get_current_token_data(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenData:
    """Dependency to get current user token data."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    return payload_to_token_data(payload)


def require_role(required_roles: List[UserRole]):
    """Dependency factory for role-based access control."""
    async def role_checker(token_data: TokenData = Depends(get_current_token_data)) -> TokenData:
        user_roles = set(token_data.roles)
        required = set(required_roles)

        # Check if user has any of the required roles
        if not user_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required)}"
            )
        return token_data

    return role_checker


# Pre-defined role dependencies
require_viewer = require_role([UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN])
require_operator = require_role([UserRole.OPERATOR, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])


# Optional authentication - returns None if no token
async def get_optional_token_data(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenData]:
    """Dependency for optional authentication."""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return payload_to_token_data(payload)
    except HTTPException:
        return None
