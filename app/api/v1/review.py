# app/api/v1/review.py
"""Review queue — list / approve / reject staged actions."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import structlog

from app.dependencies import get_current_user, get_db_dep
from app.services import review_service

log = structlog.get_logger()
router = APIRouter()


class RejectBody(BaseModel):
    reason: str = ""


@router.get("")
async def list_pending(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    return await review_service.list_pending(db)


@router.post("/{action_id}/approve")
async def approve(
    action_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    doc = await review_service.approve_action(action_id, db)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found or already resolved",
        )
    return doc


@router.post("/{action_id}/reject")
async def reject(
    action_id: str,
    body: RejectBody,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    doc = await review_service.reject_action(action_id, body.reason, db)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found or already resolved",
        )
    return doc
