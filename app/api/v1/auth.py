from fastapi import APIRouter, HTTPException, status

from app.models.auth import LoginRequest, TokenResponse
from app.services.auth_service import DEMO_USER, create_jwt, verify_credentials

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if not verify_credentials(body.email, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_jwt(DEMO_USER)
    return TokenResponse(access_token=token)
