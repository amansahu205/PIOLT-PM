# app/services/auth_service.py
"""
Auth service for PilotPM demo.
No user database — single hardcoded PM account from .env.
JWT signed with HS256.
"""

from datetime import UTC, datetime, timedelta

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

log = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USER = {
    "email": settings.DEMO_EMAIL,
    "role": "pm",
    "name": "Aman",
}


def verify_credentials(email: str, password: str) -> bool:
    """Check email + password against .env values."""
    return email == settings.DEMO_EMAIL and password == settings.DEMO_PASSWORD


def create_jwt(user: dict) -> str:
    """Create a signed JWT for the PM user."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user["email"],
        "role": user["role"],
        "name": user["name"],
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and validate JWT. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        log.warning("auth.jwt_invalid", error=str(e))
        return None
