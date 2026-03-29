# app/api/v1/blockers.py
"""
Blocker Radar router — F-002.
Pattern: thin router → service → repository.
"""

from fastapi import APIRouter, Depends, HTTPException, status

import structlog

from app.dependencies import get_current_user, get_db_dep
from app.models.blocker import BlockerCard, DismissRequest
from app.services.blocker_service import BlockerService

log = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=list[BlockerCard])
async def get_blockers(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get all active blockers. Returns empty list if none."""
    try:
        return await BlockerService.get_active_blockers(db)
    except Exception as e:
        log.error("blockers.get_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch blockers")


@router.post("/scan", response_model=list[BlockerCard])
async def scan_blockers(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Force a blocker scan across GitHub + Slack + Monday.com."""
    try:
        return await BlockerService.run_blocker_scan(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("blockers.scan_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Blocker scan failed")


@router.patch("/{blocker_id}/dismiss", response_model=BlockerCard)
async def dismiss_blocker(
    blocker_id: str,
    body: DismissRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Dismiss a blocker. Logs reason for agent improvement."""
    blocker = await BlockerService.dismiss(blocker_id, body.reason, db)
    if not blocker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blocker {blocker_id} not found",
        )
    return blocker


@router.get("/history", response_model=list[BlockerCard])
async def get_blocker_history(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get resolved blockers from the last N days."""
    return await BlockerService.get_resolved(days=days, db=db)
