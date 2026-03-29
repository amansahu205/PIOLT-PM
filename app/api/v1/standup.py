# app/api/v1/standup.py
"""F-001 Standup router — thin handlers → service."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_db_dep
from app.services.standup_service import StandupService
import structlog

log = structlog.get_logger()
router = APIRouter()


@router.get("/today")
async def get_today_standup(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    try:
        return await StandupService.get_today_digest(db)
    except Exception as e:
        log.error("standup.today_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load standup digest",
        ) from e


@router.post("/generate")
async def generate_standup(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    try:
        return await StandupService.generate_digest(db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        log.error("standup.generate_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Standup generation failed",
        ) from e


@router.get("/history")
async def standup_history(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    try:
        return await StandupService.get_history(db)
    except Exception as e:
        log.error("standup.history_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load standup history",
        ) from e
