# app/dependencies.py
"""
FastAPI dependencies.
All protected routes use: Depends(get_current_user)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.services.auth_service import decode_jwt

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Validate JWT from Authorization: Bearer <token> header.
    Returns user dict with email and role (JWT `sub` mapped to email).
    Raises 401 if invalid or expired.
    """
    token = credentials.credentials
    payload = decode_jwt(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "email": payload.get("sub", ""),
        "role": payload.get("role", ""),
        "name": payload.get("name"),
    }


async def get_db_dep() -> AsyncIOMotorDatabase:
    """MongoDB database instance for dependency injection."""
    return get_db()


# Type alias for cleaner route signatures
CurrentUser = Depends(get_current_user)
DB = Depends(get_db_dep)
